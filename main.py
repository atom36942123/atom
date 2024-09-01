#logging
import logging
logging.basicConfig(level="INFO")

#sentry
import sentry_sdk
from config import config_sentry_dsn
if False:sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#lifespan
from function import function_redis_service_init
from config import postgres_object
from fastapi import FastAPI
from contextlib import asynccontextmanager
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  await function_redis_service_init()
  await postgres_object.connect()
  yield
  await postgres_object.disconnect()
  
#app
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
from config import postgres_object
from function import function_background_create_log
from function import function_error_prepare
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  try:
    response=await api_function(request)
    path=request.url.path.split("/")
    print(path)
    if request.method in ["DELETE"]:await function_background_create_log(postgres_object,request)
  except Exception as e:
    print(traceback.format_exc())
    error="".join(e.args)
    response=await function_error_prepare(error)
    return JSONResponse(status_code=400,content=response)
  return response

#root api
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#router
from function import function_read_filename_api
response=function_read_filename_api()
filename_api_list=response["message"]
for item in filename_api_list:
  x=__import__(item)
  app.include_router(x.router)

#server start
from function import function_server_start
if __name__=="__main__":
  function_server_start(app)
