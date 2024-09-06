#logging
import logging
logging.basicConfig(level="INFO")

#sentry
import sentry_sdk
from config import config_sentry_dsn
if False:sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#lifespan
from function import function_redis_service_start
from config import postgres_object
from fastapi import FastAPI
from contextlib import asynccontextmanager
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  await function_redis_service_start()
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
from function import function_create_log
from function import function_middleware_error
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  try:
    response=await api_function(request)
    await function_create_log(postgres_object,request)
  except Exception as e:
    print(traceback.format_exc())
    response=await function_middleware_error(e.args)
    return JSONResponse(status_code=400,content=response)
  return response

#root api
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#router
from function import function_router_list
response=function_router_list()
router_list=response["message"]
for item in router_list:app.include_router(item)  
  
#server start
from function import function_server_start
if __name__=="__main__":
  function_server_start(app)
