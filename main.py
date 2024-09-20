#runtime
from config import postgres_database_url
from databases import Database
postgres_object=Database(postgres_database_url,min_size=1,max_size=100)
column_datatype=None

#logging
import logging
logging.basicConfig(level="INFO")

#sentry
from config import sentry_dsn
import sentry_sdk
if False:sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from function import redis_start
from config import redis_server_url
from function import postgres_column_datatype
@asynccontextmanager
async def lifespan(app:FastAPI):
  await redis_start(redis_server_url)
  await postgres_object.connect()
  global column_datatype
  response=await postgres_column_datatype(postgres_object)
  column_datatype=response["message"]
  yield
  await postgres_object.disconnect()
  
#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
from function import middleware_error
from function import postgres_create_log
from config import jwt_secret_key
import time
@app.middleware("http")
async def middleware(request:Request,api_function):
  try:
    start=time.time()
    request.state.postgres_object=postgres_object
    request.state.column_datatype=column_datatype
    response=await api_function(request)
    end=time.time()
    await postgres_create_log(postgres_object,request,jwt_secret_key,(end-start)*1000,["POST","GET","PUT","DELETE"])
  except Exception as e:
    print(traceback.format_exc())
    response=await middleware_error(e.args)
    return JSONResponse(status_code=400,content=response)
  return response

#router
from function import router_list
response=router_list()
router_list=response["message"]
for item in router_list:app.include_router(item)

#api root
@app.get("/")
async def root():
  return {"status":1,"message":"welcome to atom"}

#api api list
@app.get("/api-list")
def api_list():
    api_list=[route.path for route in app.routes]
    return api_list

#api postgres init
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_init
import hashlib
from config import postgres_prequery,postgres_table,postgres_column,postgres_notnull,postgres_identity,postgres_default,postgres_unique,postgres_index,postgres_postquery
@app.get("/postgres-init")
async def pinit(request:Request):
   #auth check
   if hashlib.sha256(request.headers.get("Authorization").split(" ",1)[1].encode()).hexdigest()!="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3":return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_init(postgres_object,postgres_prequery,postgres_table,postgres_column,postgres_notnull,postgres_identity,postgres_default,postgres_unique,postgres_index,postgres_postquery)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#server start
from function import server_start
if __name__=="__main__":
  server_start(app)
