#logging
import logging
logging.basicConfig(level="INFO")

#sentry
from config import config_sentry_dsn
import sentry_sdk
if False:sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#postgres object
from config import config_postgres_database_uri
from databases import Database
postgres_object={item.split("/")[-1]:Database(item,min_size=1,max_size=100) for item in config_postgres_database_uri.split(",")}

#lifespan
from config import config_redis_server_uri
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
  #postgres connect
  for k,v in postgres_object.items():await v.connect()
  #shutdown
  yield
  #postgres disconnect
  for k,v in postgres_object.items():await v.disconnect()

#app
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback
@app.middleware("http")
async def middleware(request:Request,api_function):
  #x check
  key_4th=str(request.url.path).split("/")[1]
  if key_4th not in ["","docs","openapi.json","redoc"]+[*postgres_object]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in postgres_object:request.state.postgres_object=postgres_object[key_4th]
  #api response
  try:response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response

#root api
@app.get("/")
async def function_root():
   return {"status":1,"message":f"welcome to {[*postgres_object]}"}
  
#router
from mongo import router as router_mongo
app.include_router(router_mongo)

from elastic import router as router_elasticsearch
app.include_router(router_elasticsearch)

from aws import router as router_aws
app.include_router(router_aws)

from auth import router as router_auth
app.include_router(router_auth)

from my import router as router_my
app.include_router(router_my)

from object import router as router_object
app.include_router(router_object)

from message import router as router_message
app.include_router(router_message)

from utility import router as router_utility
app.include_router(router_utility)

from admin import router as router_admin
app.include_router(router_admin)




from database import router as router_database
app.include_router(router_database)

from feed import router as router_feed
app.include_router(router_feed)

#server start
import uvicorn,asyncio
if __name__=="__main__":
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())

