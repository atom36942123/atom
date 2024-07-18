#env
from environs import Env
env=Env()
env.read_env()

#config
config_redis_url=env("redis_url")
config_x=env.list("x")
from object import postgres_object


#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
@asynccontextmanager
async def lifespan(app:FastAPI):
   try:
      #redis
      redis_object=aioredis.from_url(config_redis_url,encoding="utf-8",decode_responses=True)
      FastAPICache.init(RedisBackend(redis_object))
      await FastAPILimiter.init(redis_object)
      #postgres
      for k,v in postgres_object.items():await v.connect()
      yield for k,v in postgres_object.items():await v.disconnect()
   except Exception as e:print(e.args)

#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from function import function_http_response
@app.middleware("http")
async def middleware(request:Request,api_function):
   #x check
   if str(request.url).split("/")[3] not in ["","docs","redoc","openapi.json"]+config_x:return function_http_response(400,0,f"allowed x={str(config_x)}")
   #api response
   try:response=await api_function(request)
   except Exception as e:return function_http_response(400,0,e.args)
   #final response
   return response

#router
from api import router
app.include_router(router)
from zzz import router
app.include_router(router)

#server start
from function import function_server_start
if __name__=="__main__":function_server_start(app,"0.0.0.0",8000)
