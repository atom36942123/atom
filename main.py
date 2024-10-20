#sentry
from config import sentry_dsn
import sentry_sdk
if False:
   sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)
   print("sentry connected")
   
#postgtes client
from config import postgres_database_url
from databases import Database
postgres_client=Database(postgres_database_url,min_size=1,max_size=100)

#redis client
from config import redis_server_url
from redis import asyncio as aioredis
redis_client_1=aioredis.from_url(redis_server_url,encoding="utf-8",decode_responses=True)
redis_client_2=aioredis.from_url(redis_server_url)

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
postgres_schema_column_data_type=None
@asynccontextmanager
async def lifespan(app:FastAPI):
   #connect
   await postgres_client.connect()
   print("postgres connected")
   await FastAPILimiter.init(redis_client_1)
   print("rate limiter connected")
   FastAPICache.init(RedisBackend(redis_client_2))
   print("redis cache connected")
   #set postgres column data type
   global postgres_schema_column_data_type
   query="select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   output=await postgres_client.fetch_all(query=query,values={})
   postgres_schema_column_data_type={item["column_name"]:item["data_type"] for item in output}
   print("postgres column data type set") 
   yield
   await postgres_client.disconnect()
   print("postgres disconnected")
   await FastAPILimiter.close()
   print("rate limiter disconnected")
   
#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan)

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from config import secret_key_root,secret_key_jwt
from function import create_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback,time,jwt,json
object_list_log=[]
@app.middleware("http")
async def middleware(request:Request,api_function):
   start=time.time()
   user=None
   token=request.headers.get("Authorization").split(" ",1)[1] if request.headers.get("Authorization") else None
   api=request.url.path
   gate=api.split("/")[1]
   global object_list_log
   try:
      #auth check
      if gate not in ["","docs","openapi.json","root","auth","my","public","private","admin"]:return JSONResponse(status_code=400,content={"status":0,"message":"gate not allowed"}) 
      if gate=="root":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         if token!=secret_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token mismatch"})
      if gate=="my":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
      if gate=="private":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
      if gate=="admin":
         if not token:return JSONResponse(status_code=400,content={"status":0,"message":"token missing"})
         user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
         output=await postgres_client.fetch_all(query="select * from users where id=:id;",values={"id":user["id"]})
         user=output[0] if output else None
         if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
         if user["is_active"]==0:return JSONResponse(status_code=400,content={"status":0,"message":"user not active"})
         if not user["api_access"]:return JSONResponse(status_code=400,content={"status":0,"message":"user not admin"})
         if api not in user["api_access"].split(","):return JSONResponse(status_code=400,content={"status":0,"message":"api access denied"})
      #request state assign
      request.state.user=user
      request.state.app=app
      request.state.postgres_client=postgres_client
      request.state.postgres_schema_column_data_type=postgres_schema_column_data_type
      #api response
      response=await api_function(request)
      end=time.time()
      response_time_ms=(end-start)*1000
      #log create
      if request.url.path not in ["/"] and request.method in ["POST","GET","PUT","DELETE"]:
         object={"created_by_id":user["id"] if user else None,"api":api,"status_code":response.status_code,"response_time_ms":response_time_ms,"description":None}
         object_list_log.append(object)
         if len(object_list_log)>100:
            await create_postgres_object(postgres_client,postgres_schema_column_data_type,"background","log",object_list_log)
            object_list_log=[]
   except Exception as e:
      #catch error
      print(traceback.format_exc())
      error="".join(e.args)
      if "constraint_unique_likes" in error:error="already liked"
      if "constraint_unique_users" in error:error="user already exist"
      if "enough segments" in error:error="token issue"
      #log create
      object={"created_by_id":user["id"] if user else None,"api":api,"status_code":400,"response_time_ms":None,"description":error}
      object_list_log.append(object)
      if len(object_list_log)>100:
         await create_postgres_object(postgres_client,postgres_schema_column_data_type,"background","log",object_list_log)
         object_list_log=[]
      #final
      return JSONResponse(status_code=400,content={"status":0,"message":error})
   #final
   return response

#router
import os,glob
current_directory_path=os.path.dirname(os.path.realpath(__file__))
filepath_all_list=[item for item in glob.glob(f"{current_directory_path}/*.py")]
filename_all_list=[item.rsplit("/",1)[1].split(".")[0] for item in filepath_all_list]
filename_api_list=[item for item in filename_all_list if "api" in item]
router_list=[]
for item in filename_api_list:
   file_module=__import__(item)
   router_list.append(file_module.router)
for item in router_list:app.include_router(item)

#main
import asyncio
import uvicorn
if __name__=="__main__":
   try:
      loop=asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop.run_until_complete(uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio")).serve())
   except KeyboardInterrupt:print("main file exited")