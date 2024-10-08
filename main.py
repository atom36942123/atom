#logging
import logging
logging.basicConfig(level="INFO")

#sentry
from config import sentry_dsn
import sentry_sdk
if False:sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#postgtes object
from config import postgres_database_url
from databases import Database
postgres_object=Database(postgres_database_url,min_size=1,max_size=100)

#column datatype
column_datatype=None

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from function import redis_service_start
from config import redis_server_url
from function import postgres_column_datatype
@asynccontextmanager
async def lifespan(app:FastAPI):
  #redis start
  await redis_service_start(redis_server_url)
  #postgres connect
  await postgres_object.connect()
  #column datatype
  global column_datatype
  response=await postgres_column_datatype(postgres_object)
  column_datatype=response["message"]
  yield
  #postgres disconnect
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
import time
import traceback
from function import auth_check_middleware 
from function import jwt_token_decode
from config import jwt_secret_key
from config import root_secret_key
from function import postgres_log_create,postgres_object_create
from function import middleware_error
@app.middleware("http")
async def middleware(request:Request,api_function):
  try:
    #start
    start=time.time()
    #auth check
    response=await auth_check_middleware(request,jwt_token_decode,jwt_secret_key,root_secret_key,postgres_object)
    if response["status"]==0:return JSONResponse(status_code=400,content=response)
    user=response["message"]
    #request assign
    request.state.postgres_object=postgres_object
    request.state.user=user
    request.state.column_datatype=column_datatype
    request.state.app=app
    #api response
    response=await api_function(request)
    #end
    end=time.time()
    #log create
    if request.url.path not in ["/"] and request.method in ["POST","GET","PUT","DELETE"]:await postgres_log_create(postgres_object,postgres_object_create,column_datatype,request,user,(end-start)*1000)
  #exception
  except Exception as e:
    print(traceback.format_exc())
    response=await middleware_error(e.args)
    return JSONResponse(status_code=400,content=response)
  #final
  return response

#router
from function import router_list
response=router_list()
router_list=response["message"]
for item in router_list:app.include_router(item)
  
#server start
from function import server_start
if __name__=="__main__":
  server_start(app)
