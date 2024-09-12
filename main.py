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
  response=await postgres_column_datatype(postgres_object)
  global column_datatype
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
@app.middleware("http")
async def middleware(request:Request,api_function):
  try:
    request.state.postgres_object=postgres_object
    request.state.column_datatype=column_datatype
    response=await api_function(request)
    await postgres_create_log(postgres_object,request,jwt_secret_key)
  except Exception as e:
    print(traceback.format_exc())
    response=await middleware_error(e.args)
    return JSONResponse(status_code=400,content=response)
  return response

#root api
from fastapi import Request
@app.get("/")
async def root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#router
from function import router_list
response=router_list()
router_list=response["message"]
for item in router_list:app.include_router(item)  
  
#server start
from function import server_start
if __name__=="__main__":
  server_start(app)
