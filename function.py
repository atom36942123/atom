#postgres object update
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def function_postgres_object_update(postgres_object,config_column_datatype,mode,table,object_list):
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  if not object_list:return {"status":1,"message":"done"}
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=config_column_datatype[k]
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

#postgres database init
async def function_postgres_database_init(postgres_object):
  #config
  query_pre=["create extension if not exists postgis"]
  table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"]
  index={"id":"btree","created_at":"brin","is_deleted":"btree","is_verified":"btree","is_active":"btree","parent_table":"btree","parent_id":"btree","type":"btree","created_by_id":"btree","status":"btree","email":"btree","password":"btree","location":"gist","tag":"btree","tag_array":"gin"}
  not_null={"id":table,"created_at":table,"parent_table":["likes","bookmark","report","block","rating","comment","message"],"parent_id":["likes","bookmark","report","block","rating","comment","message"]}
  identity={"id":table}
  default=[["created_at","now()",table]]
  unique={"username":["users"],"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"]}
  query_post=["insert into users (username,password,type,is_protected) values ('atom','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','admin',1) on conflict do nothing;","create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;","CREATE OR REPLACE FUNCTION function_set_updated_at_now() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ language 'plpgsql';","CREATE OR REPLACE VIEW view_table_master AS with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),y as (select table_name,count(*) as count_column from information_schema.columns group by table_name) select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;","CREATE OR REPLACE VIEW view_column_master AS select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;","create materialized view if not exists mat_table_object_count as select relname as table_name,n_live_tup as count_object from pg_stat_user_tables order by count_object desc",]
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
  #query pre
  for item in query_pre:
    query=item
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #table
  for item in table:
    query=f"create table if not exists {item} ();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #column
  for k,v in column.items():
    for item in v[1]:
      query=f"alter table {item} add column if not exists {k} {v[0]};"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  #index
  for k,v in column.items():
    if k in index:
      for item in v[1]:
        query=f"create index concurrently if not exists index_{k}_{item} on {item} using {index[k]} ({k});"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #schema constraint
  query="select constraint_name from information_schema.constraint_column_usage;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  schema_constraint_name_list=[item["constraint_name"] for item in output]
  #schema column
  query="select * from information_schema.columns where table_schema='public';"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  schema_column=output
  #schema routine
  query="select proname from pg_proc;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  schema_routine_name_list=[item["proname"] for item in output]
  #protected
  for item in column["is_protected"][1]:
    query=f"create or replace rule rule_delete_disable_{item} as on delete to {item} where old.is_protected=1 do instead nothing;"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #not null
  for k,v in not_null.items():
    for item in v:
      state=[x["is_nullable"] for x in schema_column if x["table_name"]==item and x["column_name"]==k]
      if state[0]=="YES":
        query=f"alter table {item} alter column {k} set not null;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #identity
  for k,v in identity.items():
    for item in v:
      state=[x["is_identity"] for x in schema_column if x["table_name"]==item and x["column_name"]==k]
      if state[0]=="NO":
        query=f"alter table {item} alter column {k} add generated always as identity;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #default
  for item in default:
    for t in item[2]:
      state=[x["column_default"] for x in schema_column if x["table_name"]==t and x["column_name"]==item[0]]
      if state[0]==None:
        query=f"alter table {t} alter column {item[0]} set default {item[1]};"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #unique
  for k,v in unique.items():
    for item in v:
      constraint_name=f"constraint_unique_{k}_{item}".replace(",","_")
      if constraint_name not in schema_constraint_name_list:
        query=f"alter table {item} add constraint {constraint_name} unique ({k});"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #query post
  for item in query_post:
      if ("add constraint" in item and item.split()[5] in schema_constraint_name_list):continue
      else:
        query=item
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #trigger set updated_at
  for item in column["updated_at"][1]:
    query=f"CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_{item} BEFORE UPDATE ON {item} FOR EACH ROW EXECUTE PROCEDURE function_set_updated_at_now();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}

#auth check
import jwt,json
async def function_auth_check(mode,request,config_key_root,config_key_jwt,postgres_object,is_user_refresh,user_active_check,user_type_allowed_list):
  user=None
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=authorization_header.split(" ",1)[1]
  if mode=="root":
    if token!=config_key_root:return {"status":0,"message":"token root issue"}
  if mode=="jwt":
    user=json.loads(jwt.decode(token,config_key_jwt,algorithms="HS256")["data"])
    if is_user_refresh==1:
      query="select * from users where id=:id;"
      query_param={"id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return {"status":0,"message":"no user for token passed"}
    if user_active_check==1:
      if user["is_active"]==0:return {"status":0,"message":"user is not active"}
    if user_type_allowed_list:
      if user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}
  
#postgres verify otp
from datetime import datetime,timezone
async def function_postgtes_otp_verify(postgres_object,otp,email,mobile):
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
async def function_postgres_read_user_force(postgres_object,column,value):
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
async def function_postgres_add_action_count(postgres_object,action,object_list,object_table):
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
async def function_postgres_add_creator_key(postgres_object,object_list):
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
async def function_postgres_create_log(postgres_object,request,config_key_root,config_key_jwt):
  if request.method not in ["DELETE"]:return {"status":1,"message":"done"}
  created_by_id=None
  authorization_header=request.headers.get("Authorization")
  if authorization_header:
    token=authorization_header.split(" ",1)[1]
    if token==config_key_root:created_by_id=1
    else:created_by_id=json.loads(jwt.decode(token,config_key_jwt,algorithms="HS256")["data"])["id"]
  background=BackgroundTasks()
  query="insert into log (created_by_id,request_path,request_query_param,request_body) values (:created_by_id,:request_path,:request_query_param,:request_body);"
  query_param={"created_by_id":created_by_id,"request_path":request.url.path,"request_query_param":json.dumps(dict(request.query_params)),"request_body":json.dumps(dict(await request.body()))}
  background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
  return {"status":1,"message":"done"}

#auth
import jwt,json
async def function_auth(mode,request,config_key_root,config_key_jwt,postgres_object,user_refresh,user_active,user_type_allowed_list):
  user=None
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=authorization_header.split(" ",1)[1]
  if mode=="root":
    if token!=config_key_root:return {"status":0,"message":"token root issue"}
  if mode=="jwt":
    user=json.loads(jwt.decode(token,config_key_jwt,algorithms="HS256")["data"])
    if is_refresh==1:
      query="select * from users where id=:id;"
      query_param={"id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return {"status":0,"message":"no user for token passed"}
    if user_active==1:
      if user["is_active"]==0:return {"status":0,"message":"user is not active"}
    if user_type_allowed_list:
      if user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}

#token create
import jwt,json,time
from datetime import datetime,timedelta
async def function_token_create(user,key_jwt):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,key_jwt)
  return {"status":1,"message":token}

#redis key builder
from fastapi import Request,Response
def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
  param=":".join(param)
  return param

#router list
import os,glob
def function_router_list():
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
async def function_middleware_error(error_tuple):
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
async def function_redis_start(redis_server_url):
  FastAPICache.init(RedisBackend(aioredis.from_url(redis_server_url)))
  await FastAPILimiter.init(aioredis.from_url(redis_server_url,encoding="utf-8",decode_responses=True))
  return {"status":1,"message":"done"}

#server start
import uvicorn,asyncio
def function_server_start(app):
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())
  return {"status":1,"message":"done"}

#elasticsearch
from elasticsearch import Elasticsearch
async def function_elasticsearch(elasticsearch_username,elasticsearch_password,elasticsearch_cloud_id,mode,table,payload):
  elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
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
async def function_mongo(mongo_server_url,mode,database,table,payload):
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
