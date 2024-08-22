#token check root
import jwt
import json
from config import config_key_root
async def function_token_check_root(request):
   try:
      header_authorization=request.headers.get("Authorization")
      if not header_authorization:return {"status":0,"message":"authorization header is must"}
      token=request.headers.get("Authorization").split(" ",1)[1]
      if token!=config_key_root:return {"status":0,"message":"token root mismatch"}
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":"done"}

#token create
import jwt
import json
import time
from datetime import datetime
from datetime import timedelta
from config import config_key_jwt
async def function_token_create(request,user):
  try:
    x={"x":str(request.url.path).split("/")[1]}
    created_at_token={"created_at_token":datetime.today().strftime('%Y-%m-%d')}
    user_key={"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
    data=x|created_at_token|user_key
    data=json.dumps(data,default=str)
    expiry_time=time.mktime((datetime.now()+timedelta(days=100000)).timetuple())
    payload={"exp":expiry_time,"data":data}
    token=jwt.encode(payload,config_key_jwt)
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":token}

#token check
import jwt
import json
from config import config_key
async def function_token_check_jwt(request):
   try:
      header_authorization=request.headers.get("Authorization")
      if not header_authorization:return {"status":0,"message":"authorization header is must"}
      token=request.headers.get("Authorization").split(" ",1)[1]
      payload=jwt.decode(token,config_key_jwt,algorithms="HS256")
      data=payload["data"]
      user=json.loads(data)
      if user["x"]!=str(request.url.path).split("/")[1]:return {"status":0,"message":"token x mismatch"}
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":user}
  
#redis key
from fastapi import Request
from fastapi import Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[repr(sorted(request.query_params.items())),namespace,request.method.lower(),request.url.path]
  return ":".join(param)

#creator key
async def function_add_creator_key(postgres_object,object_list):
  try:
    if not object_list:return {"status":1,"message":object_list}
    object_list=[item|{"created_by_username":None} for item in object_list]
    user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
    if user_ids:
      query=f"select * from users where id in ({user_ids});"
      values={}
      object_user_list=await postgres_object.fetch_all(query=query,values=values)
      for x in object_list:
        for y in object_user_list:
           if x["created_by_id"]==y["id"]:
             x["created_by_username"]=y["username"]
             break
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":object_list}

#action count
async def function_add_action_count(postgres_object,object_list,object_table,action_table):
  try:
    if not object_list:return {"status":1,"message":object_list}
    key_name=f"{action_table}_count"
    object_list=[item|{key_name:0} for item in object_list]
    parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
    if parent_ids:
      query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
      values={"parent_table":object_table}
      object_action_list=await postgres_object.fetch_all(query=query,values=values)
      for x in object_list:
        for y in object_action_list:
          if x["id"]==y["parent_id"]:
            x[key_name]=y["count"]
            break
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":object_list}

#prepare where
async def function_prepare_where(where_param_raw):
  try:
    where_param={k:v.split(',',1)[1] for k,v in where_param_raw.items()}
    where_param_operator={k:v.split(',',1)[0] for k,v in where_param_raw.items()}
    key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param.items()]
    key_joined=' and '.join(key_list)
    where_string=f"where {key_joined}" if key_joined else ""
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":[where_string,where_param]}

#sanitization
import hashlib
import json
from datetime import datetime
async def function_sanitization_query_param_list(postgres_object,query_type,query_param_list):
  try:
    if query_type not in ["create","update","read"]:return {"status":0,"message":"query_type"}
    query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
    values={}
    output=await postgres_object.fetch_all(query=query,values=values)
    column_datatype={item["column_name"]:item["datatype"] for item in output}
    for index,object in enumerate(query_param_list):
      for k,v in object.items():
        datatype=column_datatype[k]
        if query_type in ["create","read","update"]:
          if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
          if datatype in ["integer","bigint"]:query_param_list[index][k]=int(v) if v else None
          if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
          if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
          if datatype in ["date","timestamp with time zone"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
        if query_type in ["create","update"]:
          if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":query_param_list}
