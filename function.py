#postgres object create
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_create(postgres_object,column_datatype,mode,table,object_list):
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  column_to_insert_list=[*object_list[0]]
  query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=column_datatype[k]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if "time" in datatype:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
  if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
  if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":"done"}
  
#read where clause
import hashlib
from datetime import datetime
async def read_where_clause(param,column_datatype):
  param={k:v for k,v in param.items() if k in column_datatype}
  param={k:v for k,v in param.items() if k not in ["location","metadata"]}
  where_key_value={k:v.split(',',1)[1] for k,v in param.items()}
  where_key_operator={k:v.split(',',1)[0] for k,v in param.items()}
  key_list=[f"({k} {where_key_operator[k]} :{k} or :{k} is null)" for k,v in where_key_value.items()]
  key_joined=' and '.join(key_list)
  where_string=f"where {key_joined}" if key_joined else ""
  for k,v in where_key_value.items():
    datatype=column_datatype[k]
    if k in ["password","google_id"]:where_key_value[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
    if "int" in datatype:where_key_value[k]=int(v) if v else None
    if datatype in ["numeric"]:where_key_value[k]=round(float(v),3) if v else None
    if "time" in datatype:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if datatype in ["date"]:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if datatype in ["ARRAY"]:where_key_value[k]=v.split(",") if v else None
  return {"status":1,"message":[where_string,where_key_value]}

#postgres object update
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_update(postgres_object,column_datatype,mode,table,object_list):
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  if not object_list:return {"status":1,"message":"done"}
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=column_datatype[k]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if "time" in datatype:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
  if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
  if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":"updated"}

#postgres parent read
async def postgres_parent_read(postgres_object,table,parent_table,order,limit,offset,created_by_id):
  query=f"select parent_id from {table} where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null) order by {order} limit {limit} offset {offset};"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_list=[item["parent_id"] for item in output]
  query=f"select * from {parent_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#postgres parent check
async def postgres_parent_check(postgres_object,table,parent_table,parent_ids,created_by_id):
  parent_ids_list=[int(item) for item in parent_ids.split(",")]
  query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null);"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_filtered=list(set([item["parent_id"] for item in output if item["parent_id"]]))
  return {"status":1,"message":parent_ids_filtered}

#postgres object ownership check
async def postgres_object_ownership_check(postgres_object,table,id,user_id):
  if table=="users":
    if id!=user_id:return {"status":0,"message":"ownership issue"}
  if table!="users":
    query=f"select * from {table} where id=:id;"
    query_param={"id":id}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    object=output[0] if output else None
    if not object:return {"status":0,"message":"no object"}
    if object["created_by_id"]!=user_id:return {"status":0,"message":"object ownership issue"}
  return {"status":1,"message":"done"}

#postgres clean
async def postgres_clean(postgres_object):
  for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
    query=f"delete from {table} where created_by_id not in (select id from users);"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  for table in ["likes","bookmark","report","block","rating","comment","message"]:
    for parent_table in ["users","post","comment"]:
      query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#csv to object list
import csv,codecs
async def csv_to_object_list(file):
  if file.content_type!="text/csv":return {"status":0,"message":"file extension must be csv"}
  file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
  object_list=[]
  for row in file_csv:
    object_list.append(row)
  await file.close()
  return {"status":1,"message":object_list}

#postgres column datatype
async def postgres_column_datatype(postgres_object):
  query="select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if output:column_datatype={item["column_name"]:item["data_type"] for item in output}
  return {"status":1,"message":column_datatype}

#auth check
import jwt,json
async def auth_check(request,jwt_secret_key,postgres_object,user_active_check,user_type_allowed_list):
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"token is must"}
  token=authorization_header.split(" ",1)[1]
  user=json.loads(jwt.decode(token,jwt_secret_key,algorithms="HS256")["data"])
  if postgres_object==1:
    query="select * from users where id=:id;"
    query_param={"id":user["id"]}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    user=output[0] if output else None
    if not user:return {"status":0,"message":"no user for token passed"}
  if user_active_check and user["is_active"]==0:return {"status":0,"message":"user is not active"}
  if user_type_allowed_list and user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}
  
#postgres verify otp
from datetime import datetime,timezone
async def postgtes_otp_verify(postgres_object,otp,email,mobile):
  if not otp:return {"status":0,"message":"otp mandatory"}
  if email and mobile:return {"status":0,"message":"only one contact allowed"}
  if not email and not mobile:return {"status":0,"message":"both contact cant be null"}
  if email:
    query="select * from otp where email=:email order by id desc limit 1;"
    query_param={"email":email}
  if mobile:
    query="select * from otp where mobile=:mobile order by id desc limit 1;"
    query_param={"mobile":mobile}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if not output:return {"status":0,"message":"otp not found"}
  if int(datetime.now(timezone.utc).strftime('%s'))-int(output[0]["created_at"].strftime('%s'))>60:return {"status":0,"message":"otp expired"}
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
  return {"status":1,"message":"otp verifed"}

#postgres read user force
async def postgres_read_user_force(postgres_object,column,value):
  if not value:return {"status":0,"message":"value mandatory"}
  query=f"select * from users where {column}=:value order by id desc limit 1;"
  query_param={"value":value}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  user=output[0] if output else None
  if not user:
    query=f"insert into users ({column}) values (:value) returning *;"
    query_param={"value":value}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    user_id=output[0]["id"]
    query="select * from users where id=:id;"
    query_param={"id":user_id}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    user=output[0]
  return {"status":1,"message":user}

#postgres add action count
async def postgres_add_action_count(postgres_object,action,object_list,object_table):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action}_count"
  object_list=[dict(item)|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}

#postgres add creator key
async def postgres_add_creator_key(postgres_object,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[dict(item)|{"created_by_username":None} for item in object_list]
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

#postgres create log
import jwt,json
from fastapi import BackgroundTasks
async def postgres_create_log(postgres_object,request,jwt_secret_key):
  #if request.method not in ["DELETE"]:return {"status":1,"message":"done"}
  created_by_id=None
  authorization_header=request.headers.get("Authorization")
  if authorization_header:created_by_id=json.loads(jwt.decode(authorization_header.split(" ",1)[1],jwt_secret_key,algorithms="HS256")["data"])["id"]
  background=BackgroundTasks()
  request_query_param=json.dumps(dict(request.query_params))
  #request_body=json.dumps(dict(request.json()))
  request_body=None
  query="insert into log (created_by_id,request_path,request_query_param,request_body) values (:created_by_id,:request_path,:request_query_param,:request_body);"
  query_param={"created_by_id":created_by_id,"request_path":request.url.path,"request_query_param":request_query_param,"request_body":request_body}
  background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
  return {"status":1,"message":"done"}

#postgres delete index all
async def postgres_delete_index_all(postgres_object):
  query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if output[0]["output"]:
    query=output[0]["output"]
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}

#token create
import jwt,json,time
from datetime import datetime,timedelta
async def token_create(user,jwt_secret_key):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,jwt_secret_key)
  return {"status":1,"message":token}

#redis key builder
from fastapi import Request,Response
def redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
  param=":".join(param)
  return param

#router list
import os,glob
def router_list():
  current_directory_path=os.path.dirname(os.path.realpath(__file__))
  filepath_all_list=[item for item in glob.glob(f"{current_directory_path}/*.py")]
  filename_all_list=[item.rsplit("/",1)[1].split(".")[0] for item in filepath_all_list]
  filename_api_list=[item for item in filename_all_list if "api" in item]
  router_list=[]
  for item in filename_api_list:
    file_module=__import__(item)
    router_list.append(file_module.router)
  return {"status":1,"message":router_list}

#middleware error
async def middleware_error(error_tuple):
  error="".join(error_tuple)
  if "constraint_unique_likes" in error:error="already liked"
  if "constraint_unique_users" in error:error="user already exist"
  if "enough segments" in error:error="token issue"
  return {"status":0,"message":error}

#redis service start
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
async def redis_start(redis_server_url):
  FastAPICache.init(RedisBackend(aioredis.from_url(redis_server_url)))
  await FastAPILimiter.init(aioredis.from_url(redis_server_url,encoding="utf-8",decode_responses=True))
  return {"status":1,"message":"done"}

#server start
import uvicorn,asyncio
def server_start(app):
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())
  return {"status":1,"message":"done"}

#elasticsearch
from elasticsearch import Elasticsearch
async def elasticsearch(elasticsearch_username,elasticsearch_password,elasticsearch_cloud_id,mode,table,payload):
  elasticsearch_object=Elasticsearch(cloud_id=elasticsearch_cloud_id,basic_auth=(elasticsearch_username,elasticsearch_cloud_id))
  if mode=="create":
    id,data=payload["id"],payload["data"]
    output=elasticsearch_object.index(index=table,id=id,document=data)
  if mode=="read":
    id=payload["id"]
    response=elasticsearch_object.get(index=table,id=id)
  if mode=="update":
    id,data=payload["id"],payload["data"]
    response=elasticsearch_object.update(index=table,id=id,doc=request_body)
  if mode=="delete":
    id=payload["id"]
    response=elasticsearch_object.delete(index=table,id=id)
  if mode=="refresh_table":
    response=elasticsearch_object.indices.refresh(index=table)
  if mode=="search":
    key,value,limit=payload["key"],payload["value"],payload["limit"]
    response=elasticsearch_object.search(index=table,body={"query":{"match":{key:value}},"size":limit})
  return {"status":1,"message":output}
  
#mongo
import motor.motor_asyncio
from bson import ObjectId
async def mongo(mongo_server_url,mode,database,table,payload):
  mongo_object=motor.motor_asyncio.AsyncIOMotorClient(mongo_server_url)
  if mode=="create":
    if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(payload)
      output={"status":1,"message":repr(output.inserted_id)}
  if mode=="read":
    if database=="test" and table=="users":
      id=payload["id"]
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
  if mode=="update":
    if database=="test" and table=="users":
      id,data=payload["id"],payload["data"]
      output=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":data})
      output={"status":1,"message":output.modified_count}
  if mode=="delete":
    if database=="test" and table=="users":
      id=payload["id"]
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
      output={"status":1,"message":output.deleted_count}
  return {"status":1,"message":output}

#postgres init
async def postgres_init(postgres_object):
  #config
  prequery=["create extension if not exists postgis"]
  postquery=["insert into users (username,password,type,is_protected) values ('atom','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','admin',1) on conflict do nothing;","create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;","CREATE OR REPLACE FUNCTION set_updated_at_now() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ language 'plpgsql';","CREATE OR REPLACE VIEW view_table_master AS with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),y as (select table_name,count(*) as count_column from information_schema.columns group by table_name) select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;","CREATE OR REPLACE VIEW view_column_master AS select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;","create materialized view if not exists mat_table_object_count as select relname as table_name,n_live_tup as count_object from pg_stat_user_tables order by count_object desc",]
  table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"]
  notnull={"id":table,"created_at":table,"parent_table":["likes","bookmark","report","block","rating","comment","message"],"parent_id":["likes","bookmark","report","block","rating","comment","message"]}
  identity={"id":table}
  default=[["created_at","now()",table]]
  unique={"username":["users"],"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"]}
  index={"id":["btree",table],"created_at":["brin",table],"created_by_id":["btree",table],"is_deleted":["btree",table],"is_active":["btree",["users","post"]],"is_verified":["btree",["users","post"]],"parent_table":["btree",["likes","bookmark","report","block","rating","comment","message"]],"parent_id":["btree",["likes","bookmark","report","block","rating","comment","message"]],"type":["btree",["users","post","box","atom","helpdesk"]],"status":["btree",["report","helpdesk","message"]],"email":["btree",["users","post","box","atom","otp","helpdesk"]],"password":["btree",["users"]],"location":["gist",["users","post","box","atom"]],"tag":["btree",["users","post","box","atom"]],"tag_array":["gin",["atom"]],}
  column={
  "id":["bigint",table],
  "created_at":["timestamptz",table],
  "created_by_id":["bigint",table],
  "is_deleted":["int",table],
  "updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
  "updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
  "is_active":["int",["users","post"]],
  "is_verified":["int",["users","post"]],
  "is_protected":["int",["users","post","box","atom"]],
  "parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
  "parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
  "type":["text",["users","post","box","atom","helpdesk"]],
  "status":["text",["report","helpdesk","message"]],
  "remark":["text",["report","helpdesk"]],
  "rating":["numeric",["rating","atom","post"]],
  "metadata":["jsonb",["users","post","box","atom"]],
  "username":["text",["users"]],
  "password":["text",["users"]],
  "google_id":["text",["users"]],
  "profile_pic_url":["text",["users"]],
  "last_active_at":["timestamptz",["users"]],
  "name":["text",["users"]],
  "email":["text",["users","post","box","atom","otp","helpdesk"]],
  "mobile":["text",["users","post","box","atom","otp","helpdesk"]],
  "date_of_birth":["date",["users"]],
  "title":["text",["users","post","box","atom"]],
  "description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
  "file_url":["text",["post","box","atom","comment","message"]],
  "link_url":["text",["post","box","atom"]],
  "tag":["text",["users","post","box","atom"]],
  "otp":["int",["otp"]],
  "tag_array":["text[]",["atom"]],
  "location":["geography(POINT)",["users","post","box","atom"]],
  "request_path":["text",["log"]],
  "request_query_param":["jsonb",["log"]],
  "request_body":["jsonb",["log"]],
  "interest":["text",["users"]],
  "skill":["text",["users"]],
  "gender":["text",["users"]],
  "country":["text",["users"]],
  "state":["text",["users"]],
  "city":["text",["users"]],
  }
  #prequery/table/column/protected/postquery/trigger/index
  for item in prequery:output=await postgres_object.fetch_all(query=item,values={})
  for item in table:await postgres_object.fetch_all(query=f"create table if not exists {item} ();",values={})
  [await postgres_object.fetch_all(query=f"alter table {item} add column if not exists {k} {v[0]};",values={}) for k,v in column.items() for item in v[1]]
  for item in column["is_protected"][1]:await postgres_object.fetch_all(query=f"create or replace rule rule_delete_disable_{item} as on delete to {item} where old.is_protected=1 do instead nothing;",values={})
  [await postgres_object.fetch_all(query=item,values={}) for item in postquery if ("add constraint" in item and item.split()[5] in schema_constraint_name_list)]
  for item in column["updated_at"][1]:await postgres_object.fetch_all(query=f"CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_{item} BEFORE UPDATE ON {item} FOR EACH ROW EXECUTE PROCEDURE set_updated_at_now();",values={})
  [await postgres_object.fetch_all(query=f"create index concurrently if not exists index_{k}_{item} on {item} using {v[0]} ({k});",values={}) for k,v in index.items() for item in v[1]]
  #schema
  output=await postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
  schema_constraint_name_list=[item["constraint_name"] for item in output]
  output=await postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
  schema_column=output
  output=await postgres_object.fetch_all(query="select proname from pg_proc;",values={})
  schema_routine_name_list=[item["proname"] for item in output]
  schema_column_table_nullable={item["column_name"]+"_"item["table_name"]:item["is_nullable"] for item in schema_column}
  schema_column_table_identity={item["column_name"]+"_"item["table_name"]:item["is_identity"] for item in schema_column}
  schema_column_table_default={item["column_name"]+"_"item["table_name"]:item["column_default"] for item in schema_column}
  #notnull/identity/default/unique
  [await postgres_object.fetch_all(query=f"alter table {item} alter column {k} set not null;",values={}) for k,v in notnull.items() for item in v if schema_column_table_nullable[f"{k}_{item}"]=="YES"]
  [await postgres_object.fetch_all(query=f"alter table {item} alter column {k} add generated always as identity;",values={}) for k,v in identity.items() for item in v if schema_column_table_identity[f"{k}_{item}"]=="NO"]
  [await postgres_object.fetch_all(query=f"alter table {t} alter column {item[0]} set default {item[1]};",values={})for item1 in default for item2 in item[2] if schema_column_table_default[f"{item1}_{item2}"]==None]
  [await postgres_object.fetch_all(query=f"alter table {item} add constraint constraint_unique_{k}_{item} unique ({k});".replace(",","_"),values={}) for k,v in unique.items() for item in v if f"constraint_unique_{k}_{item}".replace(",","_") not in schema_constraint_name_list]
  return {"status":1,"message":"done"}
  
