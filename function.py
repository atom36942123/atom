#postgres location search
async def postgres_location_search(postgres_object,table,location,within,order,limit,offset,where_string,where_value):
  long,lat=float(location.split(",")[0]),float(location.split(",")[1])
  min_meter,max_meter=int(within.split(",")[0]),int(within.split(",")[1])
  query=f'''
  with
  x as (select * from {table} {where_string}),
  y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x)
  select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {offset};
  '''
  query_param=where_value
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#where clause
import hashlib
from datetime import datetime
async def where_clause(param,column_datatype):
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
  
#postgres object create
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_create(postgres_object,column_datatype,mode,table,object_list):
  if not object_list:return {"status":0,"message":"object list empty"}
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  column_to_insert_list=[*object_list[0]]
  query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=column_datatype[k]
      if not v:query_param_list[index][k]=None
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if "time" in datatype:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
  output=None
  if len(object_list)==1:
    if mode=="background":background.add_task(await postgres_object.fetch_all(query=query,values=query_param_list[0]))
    if mode=="normal":output=await postgres_object.fetch_all(query=query,values=query_param_list[0])
  else:
    if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
    if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":output}
  
#postgres object update
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def postgres_object_update(postgres_object,column_datatype,mode,table,object_list):
  if not object_list:return {"status":0,"message":"object list empty"}
  background=BackgroundTasks()
  if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=column_datatype[k]
      if not v:query_param_list[index][k]=None
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if "time" in datatype:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if datatype in ["ARRAY"]:query_param_list[index][k]=v.split(",") if v else None
  output=None
  if len(object_list)==1:
    if mode=="background":background.add_task(await postgres_object.fetch_all(query=query,values=query_param_list[0]))
    if mode=="normal":output=await postgres_object.fetch_all(query=query,values=query_param_list[0])
  else:
    if mode=="background":background.add_task(await postgres_object.execute_many(query=query,values=query_param_list))
    if mode=="normal":output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":output}

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
  column_datatype={item["column_name"]:item["data_type"] for item in output}
  return {"status":1,"message":column_datatype}

#postgres otp verify
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
  if int(datetime.now(timezone.utc).strftime('%s'))-int(output[0]["created_at"].strftime('%s'))>6000000000000:return {"status":0,"message":"otp expired"}
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
  return {"status":1,"message":"otp verifed"}

#postgres add action count
async def postgres_add_action_count(postgres_object,action,object_table,object_list):
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

#auth check middleware
import jwt,json
async def auth_check_middleware(request,jwt_token_decode,jwt_secret_key,postgres_object):
  user=None
  path=request.url.path
  for item in ["/my","/private","/admin"]:
    if item in path:
      if item=="/admin":response=await jwt_token_decode(request,jwt_secret_key,postgres_object)
      else:response=await jwt_token_decode(request,jwt_secret_key,None)
      if response["status"]==0:return response
      user=response["message"]
  if "/admin" in path and user["is_active"]==0:return {"status":0,"message":"user not active"}
  if "/admin" in path and not user["api_access"]:return {"status":0,"message":"api access denied"}
  if "/admin" in path and path not in user["api_access"].split(","):return {"status":0,"message":"api access denied"}
  return {"status":1,"message":user}

#jwt token decode
import jwt,json
async def jwt_token_decode(request,jwt_secret_key,postgres_object):
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"token is must"}
  token=authorization_header.split(" ",1)[1]
  user=json.loads(jwt.decode(token,jwt_secret_key,algorithms="HS256")["data"])
  if postgres_object:
    query="select * from users where id=:id;"
    query_param={"id":user["id"]}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    user=output[0] if output else None
    if not user:return {"status":0,"message":"no user for token passed"}
  return {"status":1,"message":user}
  
#jwt token encode
import jwt,json,time
from datetime import datetime,timedelta
async def jwt_token_encode(user,jwt_secret_key):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"],"is_protected":user["is_protected"]}
  data=json.dumps(data,default=str)
  expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,jwt_secret_key)
  return {"status":1,"message":token}

#postgres create log
import jwt,json
from fastapi import BackgroundTasks
async def postgres_create_log(postgres_object,request,jwt_secret_key,response_time_ms,request_method_allowed):
  request_url_path=request.url.path
  if len(request_url_path.split("/"))==2:return None
  if request.method not in request_method_allowed:return None
  request_query_param=json.dumps(dict(request.query_params))
  request_body=None
  created_by_id=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],jwt_secret_key,algorithms="HS256")["data"])["id"] if request.headers.get("Authorization") else None
  query="insert into log (created_by_id,request_url_path,request_query_param,request_body,response_time_ms) values (:created_by_id,:request_url_path,:request_query_param,:request_body,:response_time_ms);"
  query_param={"created_by_id":created_by_id,"request_url_path":request_url_path,"request_query_param":request_query_param,"request_body":request_body,"response_time_ms":response_time_ms}
  background=BackgroundTasks()
  background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
  return {"status":1,"message":"done"}

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
async def redis_service_start(redis_server_url):
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
