#logging
import logging
logging.basicConfig(level="INFO")

#sentry
import sentry_sdk
from config import config_sentry_dsn
if False:sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#lifespan
from config import config_redis_server
from config import postgres_object
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  #redis cache
  FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_server)))
  #redis rate limiter
  await FastAPILimiter.init(aioredis.from_url(config_redis_server,encoding="utf-8",decode_responses=True))
  #postgres object connect
  await postgres_object.connect()
  yield
  #postgres object disconnect
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
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  try:
    #api response
    response=await api_function(request)
    #create log
    if request.method in ["DELETE"]:await function_background_create_log(postgres_object,request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content={"status":0,"message":e.args})
  return response

#root api
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#router
import os
import glob
current_directory_path=os.path.dirname(os.path.realpath(__file__))
file_path_all_list=[item for item in glob.glob(f"{current_directory_path}/*.py")]
file_name_all_list=[item.rsplit("/",1)[1].split(".")[0] for item in file_path_all_list]
file_name_api_list=[item for item in file_name_all_list if "api" in item]
for item in file_name_api_list:
  x=__import__(item)
  app.include_router(x.router)

#server start
import uvicorn
import asyncio
if __name__=="__main__":
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())
