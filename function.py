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
async def function_token_create(user,config_key_jwt):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  config_token_expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=config_token_expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,config_key_jwt)
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
