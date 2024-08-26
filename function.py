#csv
import csv,codecs
async def function_csv(postgres_object,mode,table,file,function_sanitization_query_param_list):
  if mode not in ["create","update"]:return {"status":0,"message":"wrong mode"}
  if file.content_type!="text/csv":return {"status":0,"message":"file must be csv"}
  file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
  file_row_list=[]
  for row in file_csv:file_row_list.append(row)
  if mode=="create":
    column_to_insert_list=[*file_row_list[0]]
    query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
    query_param_list=file_row_list
  if mode=="update":
    column_to_update_list=[*file_row_list[0]]
    column_to_update_list.remove("id")
    query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
    query_param_list=file_row_list
  response=await function_sanitization_query_param_list(postgres_object,"create",query_param_list)
  if response["status"]==0:return response
  query_param=response["message"]
  output=await postgres_object.execute_many(query=query,values=query_param)
  await file.close()
  return {"status":1,"message":"done"}

#auth check
import jwt,json
from config import config_key_jwt,config_key_root
async def function_auth_check(request,mode,user_type_allowed_list):
  if mode not in ["jwt","root"]:return {"status":0,"message":"wrong mode"}
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=request.headers.get("Authorization").split(" ",1)[1]
  user=None
  if mode=="root":
    if token!=config_key_root:return {"status":0,"message":"token root issue"}
  if mode=="jwt":
    payload=jwt.decode(token,config_key_jwt,algorithms="HS256")
    data=payload["data"]
    user=json.loads(data)
    if user_type_allowed_list:
      if user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}

#token check jwt
import jwt,json
from config import config_key_jwt
async def function_token_check_jwt(request):
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=request.headers.get("Authorization").split(" ",1)[1]
  payload=jwt.decode(token,config_key_jwt,algorithms="HS256")
  data=payload["data"]
  user=json.loads(data)
  return {"status":1,"message":user}

#token create jwt
import jwt,json,time
from datetime import datetime,timedelta
from config import config_key_jwt
async def function_token_create_jwt(user):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  config_token_expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=config_token_expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,config_key_jwt)
  return {"status":1,"message":token}

#redis key
from fastapi import Request,Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[repr(sorted(request.query_params.items())),namespace,request.method.lower(),request.url.path]
  param=":".join(param)
  return param

#prepare where
async def function_prepare_where(where_param_raw):
  where_param={k:v.split(',',1)[1] for k,v in where_param_raw.items()}
  where_param_operator={k:v.split(',',1)[0] for k,v in where_param_raw.items()}
  key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param.items()]
  key_joined=' and '.join(key_list)
  where_string=f"where {key_joined}" if key_joined else ""
  return {"status":1,"message":[where_string,where_param]}

#sanitization
import hashlib,json
from datetime import datetime
from config import config_database_column
async def function_sanitization_query_param_list(postgres_object,query_type,query_param_list):
  if query_type not in ["create","update","read"]:return {"status":0,"message":"wrong query_type"}
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=config_database_column[k][0]
      if query_type in ["create","read","update"]:
        if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
        if datatype in ["bigint","int"]:query_param_list[index][k]=int(v) if v else None
        if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
        if datatype in ["timestamptz","date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
        if "[]" in datatype:query_param_list[index][k]=v.split(",") if v else None
      if query_type in ["create","update"]:
        if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
  return {"status":1,"message":query_param_list}

#creator key
async def function_add_creator_key(postgres_object,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[item|{"created_by_username":None} for item in object_list]
  user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
  if user_ids:
    query=f"select * from users where id in ({user_ids});"
    query_param={}
    object_user_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_user_list:
         if x["created_by_id"]==y["id"]:
           x["created_by_username"]=y["username"]
           break
  return {"status":1,"message":object_list}

#action count
async def function_add_action_count(postgres_object,object_list,object_table,action_table):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action_table}_count"
  object_list=[item|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}
  
#delete index all
async def function_delete_index_all(postgres_object):
  query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if output[0]["output"]:
    query=output[0]["output"]
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}
