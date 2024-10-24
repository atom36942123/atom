#sentry
from config import sentry_dsn
import sentry_sdk
if False:sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)
   
#postgtes client
from config import postgres_database_url
from databases import Database
postgres_client=Database(postgres_database_url,min_size=1,max_size=100)

#redis client
from config import redis_server_url
import redis.asyncio as redis
pool=redis.ConnectionPool.from_url(redis_server_url)
redis_client=redis.Redis.from_pool(pool)

#mongo client
import motor.motor_asyncio
if False:mongo_client=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
postgres_column_data_type=None
@asynccontextmanager
async def lifespan(app:FastAPI):
   #postgres connect
   await postgres_client.connect()
   print("postgres connected")
   #redis
   print("redis status:",await redis_client.ping())
   #ratelimiter connect
   await FastAPILimiter.init(redis_client)
   print("rate limiter connected")
   #cache connect
   FastAPICache.init(RedisBackend(redis_client))
   print("redis cache connected")
   #set postgres schema column data type
   global postgres_column_data_type
   query="select column_name,count(*),max(data_type) as data_type,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   output=await postgres_client.fetch_all(query=query,values={})
   postgres_column_data_type={item["column_name"]:item["data_type"] for item in output}
   print("postgres column data type set") 
   yield
   #postgres disconnect
   await postgres_client.disconnect()
   print("postgres disconnected")
   #ratelimiter disconnect
   await FastAPILimiter.close()
   print("rate limiter disconnected")
   #redis disconnect
   await redis_client.aclose()
   await pool.aclose()
   print("redis disconnected")
   
#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan)

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from config import secret_key_root
from config import secret_key_jwt
from function import create_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
import time,jwt,json,traceback
object_list_log=[]
@app.middleware("http")
async def middleware(request:Request,api_function):
   start=time.time()
   user=None
   token=request.headers.get("Authorization").split(" ",1)[1] if request.headers.get("Authorization") else None
   api=request.url.path
   gate=api.split("/")[1]
   try:
      #auth check
      if gate not in ["","docs","openapi.json","root","auth","my","public","private","admin"]:return JSONResponse(status_code=400,content={"status":0,"message":"gate not allowed"}) 
      if gate=="root" and token!=secret_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token mismatch"})
      if gate=="my":user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
      if gate=="private":user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
      if gate=="admin":
         user=json.loads(jwt.decode(token,secret_key_jwt,algorithms="HS256")["data"])
         output=await postgres_client.fetch_all(query="select * from users where id=:id;",values={"id":user["id"]})
         user=output[0] if output else None
         if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
         if user["is_active"]==0:return JSONResponse(status_code=400,content={"status":0,"message":"user not active"})
         if not user["api_access"]:return JSONResponse(status_code=400,content={"status":0,"message":"user not admin"})
         if api not in user["api_access"].split(","):return JSONResponse(status_code=400,content={"status":0,"message":"api access denied"})
      #request state assign
      request.state.app=app
      request.state.user=user
      request.state.postgres_client=postgres_client
      request.state.postgres_column_data_type=postgres_column_data_type
      #api response
      response=await api_function(request)
      end=time.time()
      response_time_ms=(end-start)*1000
      response_status_code=response.status_code
      #log create
      if True and request.url.path not in ["/"] and request.method in ["POST","GET","PUT","DELETE"]:
         global object_list_log
         object={"created_by_id":user["id"] if user else None,"api":api,"status_code":response_status_code,"response_time_ms":response_time_ms}
         object_list_log.append(object)
         if len(object_list_log)>100:
            await create_postgres_object(postgres_client,"log",object_list_log,"background",None)
            object_list_log=[]
   except Exception as e:
      print(traceback.format_exc())
      return JSONResponse(status_code=400,content={"status":0,"message":"".join(e.args)})
   #final
   return response

#router(api_<filename>)
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