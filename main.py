#logging
import logging
logging.basicConfig(level="INFO")

#sentry
from config import config_sentry_dsn
import sentry_sdk
if False:sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#lifespan
from config import config_redis_server_uri
from postgres import postgres_object_dict
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  #redis cache
  FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_server_uri)))
  #redis rate limiter
  await FastAPILimiter.init(aioredis.from_url(config_redis_server_uri,encoding="utf-8",decode_responses=True))
  #postgres object connect
  for k,v in postgres_object_dict.items():await v.connect()
  yield
  #postgres object disconnect
  for k,v in postgres_object_dict.items():await v.disconnect()

#app
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from postgres import postgres_object_dict
from fastapi import Request
import traceback
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  #key_4th
  key_4th=str(request.url.path).split("/")[1]
  #key_4th check
  if key_4th not in ["","docs","openapi.json","redoc"]+[*postgres_object_dict]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in postgres_object_dict:request.state.postgres_object=postgres_object_dict[key_4th]
  #api response
  try:response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response

#app import
# from router import *

mylist = [f for f in glob.glob("*.txt")]
print(mylist)

#api root
from postgres import postgres_object_dict
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
  return {"status":1,"message":f"welcome to {[*postgres_object_dict]}"}

#server start
from app import app
import uvicorn
import asyncio
if __name__=="__main__":
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())
