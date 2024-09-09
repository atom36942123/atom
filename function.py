#message delete
async def function_message_delete(postgres_object,parent_table,mode,user_id,id):
  if mode=="created":
    query="delete from message where parent_table=:parent_table and created_by_id=:created_by_id;"
    query_param={"parent_table":"users","created_by_id":user_id}
  if mode=="received":
    query="delete from message where parent_table=:parent_table and parent_id=:parent_id;"
    query_param={"parent_table":"users","parent_id":user_id}
  if mode=="all":
    query="delete from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id);"
    query_param={"parent_table":"users","created_by_id":user_id,"parent_id":user_id}
  if mode=="single":
    query="delete from message where parent_table=:parent_table and id=:id and (created_by_id=:created_by_id or parent_id=:parent_id);"
    query_param={"parent_table":"users","id":id,"created_by_id":user_id,"parent_id":user_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}
  
#message read
async def function_message_read(postgres_object,parent_table,mode,user_id,user_id_2,order,limit,offset):
  if mode=="received":
    query=f"select * from message where parent_table=:parent_table and parent_id=:parent_id order by {order} limit {limit} offset {offset};"
    query_param={"parent_table":"users","parent_id":user_id}
  if mode=="received_unread":
    query=f"select * from message where parent_table=:parent_table and parent_id=:parent_id and status is null order by {order} limit {limit} offset {offset};"
    query_param={"parent_table":"users","parent_id":user_id}
  if mode=="inbox":
    query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {offset}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
    query_param={"parent_table":"users","created_by_id":user_id,"parent_id":user_id}
  if mode=="inbox_unread":
    query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {offset};"
    query_param={"parent_table":"users","created_by_id":user_id,"parent_id":user_id}
  if mode=="thread":
    query=f"select * from message where parent_table=:parent_table and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {offset};"
    query_param={"user_1":user_id,"user_2":user_id_2}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#where prepare
import hashlib
from datetime import datetime
from config import config_database_column
async def function_where_prepare(where_param_raw):
  where_param={k:v.split(',',1)[1] for k,v in where_param_raw.items()}
  where_param_operator={k:v.split(',',1)[0] for k,v in where_param_raw.items()}
  key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param.items()]
  key_joined=' and '.join(key_list)
  where_string=f"where {key_joined}" if key_joined else ""
  for k,v in where_param.items():
    datatype=config_database_column[k][0]
    if k in ["password","google_id"]:where_param[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
    if datatype in ["bigint","int"]:where_param[k]=int(v) if v else None
    if datatype in ["numeric"]:where_param[k]=round(float(v),3) if v else None
    if datatype in ["timestamptz","date"]:where_param[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if "[]" in datatype:where_param[k]=v.split(",") if v else None
  return {"status":1,"message":[where_string,where_param]}

#object update
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
from config import config_database_column
async def function_object_update(postgres_object,mode,table,object_list):
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  if not object_list:return {"status":1,"message":"done"}
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    if "updated_by_id" not in object:return {"status":0,"message":"updated_by_id missing"}
    for k,v in object.items():
      datatype=config_database_column[k][0]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if datatype in ["bigint","int"]:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if datatype in ["timestamptz","date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if "[]" in datatype:query_param_list[index][k]=v.split(",") if v else None
  if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
  if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":"updated"}
  
#object create
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
from config import config_database_column
async def function_object_create(postgres_object,mode,table,object_list):
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  column_to_insert_list=[*object_list[0]]
  query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=config_database_column[k][0]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if datatype in ["bigint","int"]:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if datatype in ["timestamptz","date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if "[]" in datatype:query_param_list[index][k]=v.split(",") if v else None
  if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
  if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":"done"}
  
#verify otp
from datetime import datetime,timezone
async def function_otp_verify(postgres_object,otp,email,mobile):
  if email and mobile:return {"status":0,"message":"only one contact allowed"}
  if not email and not mobile:return {"status":0,"message":"only one contact is mandatory"}
  if email:
    query="select * from otp where email=:email order by id desc limit 1;"
    query_param={"email":email}
  if mobile:
    query="select otp from otp where mobile=:mobile order by id desc limit 1;"
    query_param={"mobile":mobile}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if not output:return {"status":0,"message":"otp not found"}
  print((datetime.now(timezone.utc)-output[0]["created_at"])
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
  return {"status":1,"message":"otp verifed"}

#read user force
async def function_read_user_force(postgres_object,column,value):
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

#auth check
import jwt,json
from config import config_key_jwt
from config import config_key_root
async def function_auth_check(mode,request,postgres_object,user_active_check,user_type_allowed_list):
  user=None
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=authorization_header.split(" ",1)[1]
  if mode=="root" and token!=config_key_root:return {"status":0,"message":"token root issue"}
  if mode=="jwt":user=json.loads(jwt.decode(token,config_key_jwt,algorithms="HS256")["data"])
  if user and postgres_object:
    query="select * from users where id=:id;"
    query_param={"id":user["id"]}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    user=output[0] if output else None
    if not user:return {"status":0,"message":"no user for token passed"}
  if user and user_active_check and user["is_active"]==0:return {"status":0,"message":"user is not active"}
  if user and user_type_allowed_list and user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}

#token create
import jwt,json,time
from config import config_key_jwt
from datetime import datetime,timedelta
async def function_token_create(user):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  config_token_expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=config_token_expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,config_key_jwt)
  return {"status":1,"message":token}

#create log
import jwt,json
from fastapi import BackgroundTasks
from config import config_key_jwt,config_key_root
async def function_create_log(postgres_object,request):
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

#database clean
async def function_database_clean(postgres_object):
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

#search location
async def function_search_location(postgres_object,table,where_string,where_param,location,within,order,limit,offset):
  lat,long=float(location.split(",")[0]),float(location.split(",")[1])
  min_meter,max_meter=int(within.split(",")[0]),int(within.split(",")[1])
  query=f'''
  with
  x as (select * from {table} {where_string}),
  y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x)
  select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {offset};
  '''
  query_param=where_param
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#object ownership check
async def function_object_ownership_check(postgres_object,table,id,user_id):
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

#parent check
async def function_parent_check(postgres_object,table,parent_table,parent_ids,created_by_id):
  parent_ids_list=[int(item) for item in parent_ids.split(",")]
  query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null);"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_filtered=list(set([item["parent_id"] for item in output if item["parent_id"]]))
  return {"status":1,"message":parent_ids_filtered}

#parent read
async def function_parent_read(postgres_object,table,parent_table,created_by_id,order,limit,offset):
  query=f"select parent_id from {table} where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null) order by {order} limit {limit} offset {offset};"
  query_param={"parent_table":parent_table,"created_by_id":created_by_id}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  parent_ids_list=[item["parent_id"] for item in output]
  query=f"select * from {parent_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}
  
#action count
async def function_add_action_count(postgres_object,object_list,object_table,action_table):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action_table}_count"
  object_list=[dict(item)|{key_name:0} for item in object_list]
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

#creator key
async def function_add_creator_key(postgres_object,object_list):
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

#query dict runner
async def function_query_dict_runner(postgres_object,query_dict):
  temp={}
  for k,v in query_dict.items():
    query=v
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    temp[k]=output
  return {"status":1,"message":temp}

#file to object list
import csv,codecs
async def function_file_to_object_list(file):
  if file.content_type!="text/csv":return {"status":0,"message":"file extension must be csv"}
  file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
  object_list=[]
  for row in file_csv:
    object_list.append(row)
  await file.close()
  return {"status":1,"message":object_list}

#redis service start
from config import config_redis_server_url
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
async def function_redis_service_start():
  FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_server_url)))
  await FastAPILimiter.init(aioredis.from_url(config_redis_server_url,encoding="utf-8",decode_responses=True))
  return {"status":1,"message":"done"}
  
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

#middleware error
async def function_middleware_error(error_tuple):
  error="".join(error_tuple)
  if "constraint_unique_likes" in error:error="already liked"
  if "constraint_unique_users" in error:error="user already exist"
  return {"status":0,"message":error}

#redis key
from fastapi import Request,Response
def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
  param=":".join(param)
  return param

#server start
import uvicorn,asyncio
def function_server_start(app):
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())
  return {"status":1,"message":"done"}

#database init
from config import config_database_extension,config_database_table,config_database_column,config_database_index
from config import config_database_not_null,config_database_identity,config_database_default,config_database_unique,config_database_query
async def function_database_init(postgres_object):
  #extension
  for item in config_database_extension:
    query=f"create extension if not exists {item};"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #table
  for item in config_database_table:
    query=f"create table if not exists {item} ();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #column
  for k,v in config_database_column.items():
    for table in v[1]:
      query=f"alter table {table} add column if not exists {k} {v[0]};"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  #index
  for k,v in config_database_column.items():
    if k in config_database_index:
      for table in v[1]:
        query=f"create index concurrently if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
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
  if False:
    query="select proname from pg_proc;"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    schema_routine_name_list=[item["proname"] for item in output]
  #protected
  for item in config_database_column["is_protected"][1]:
    query=f"create or replace rule rule_delete_disable_{item} as on delete to {item} where old.is_protected=1 do instead nothing;"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #not null
  for k,v in config_database_not_null.items():
    for table in v:
      state=[item["is_nullable"] for item in schema_column if item["table_name"]==table and item["column_name"]==k]
      if state[0]=="YES":
        query=f"alter table {table} alter column {k} set not null;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #identity
  for k,v in config_database_identity.items():
    for table in v:
      state=[column["is_identity"] for column in schema_column if column["table_name"]==table and column["column_name"]==k]
      if state[0]=="NO":
        query=f"alter table {table} alter column {k} add generated always as identity;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #default
  for item in config_database_default:
    for table in item[2]:
      state=[column["column_default"] for column in schema_column if column["table_name"]==table and column["column_name"]==item[0]]
      if state[0]==None:
        query=f"alter table {table} alter column {item[0]} set default {item[1]};"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #unique
  for k,v in config_database_unique.items():
    for table in v:
      constraint_name=f"constraint_unique_{k}_{table}".replace(",","_")
      if constraint_name not in schema_constraint_name_list:
        query=f"alter table {table} add constraint {constraint_name} unique ({k});"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #query
  for item in config_database_query:
      if ("add constraint" in item and item.split()[5] in schema_constraint_name_list):continue
      else:
        query=item
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #trigger set updated_at
  for item in config_database_column["updated_at"][1]:
    query=f"CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_{item} BEFORE UPDATE ON {item} FOR EACH ROW EXECUTE PROCEDURE function_set_updated_at_now();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}

#s3
from config import config_aws_access_key_id,config_aws_secret_access_key
from config import  config_s3_bucket_name,config_s3_region_name
import boto3,uuid
async def function_s3(mode,filename,url):
  s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="create_url":output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=str(uuid.uuid4())+"-"+filename,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
  if mode=="delete_url":output=s3_resource.Object(config_s3_bucket_name,url.rsplit("/",1)[1]).delete()
  if mode=="delete_all":output=s3_resource.Bucket(config_s3_bucket_name).objects.all().delete()
  return {"status":1,"message":output}

#ses
from config import config_aws_access_key_id,config_aws_secret_access_key
from config import config_ses_sender_email,config_ses_region_name
import boto3
async def function_ses(mode,to,title,description):
  ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="send_email":output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
  return {"status":1,"message":output}

#elasticsearch
from config import config_elasticsearch_username,config_elasticsearch_password,config_elasticsearch_cloud_id
from elasticsearch import Elasticsearch
async def function_elasticsearch(mode,table,payload):
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
from config import config_mongo_server_url
import motor.motor_asyncio
from bson import ObjectId
async def function_mongo(mode,database,table,payload):
  mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_url)
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
