#env
from environs import Env
env=Env()
env.read_env()

#postgres
from databases import Database
postgres_object={x.split("/")[-1]:Database(x,min_size=1,max_size=100) for x in env.list("postgres")}

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
      redis_object=aioredis.from_url("redis://127.0.0.1",encoding="utf-8",decode_responses=True)
      FastAPICache.init(RedisBackend(redis_object))
      await FastAPILimiter.init(redis_object)
      #postgres
      for k,v in postgres_object.items():await v.connect()
      yield 
      for k,v in postgres_object.items():await v.disconnect()
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
   x=str(request.url).split("/")[3]
   if x not in ["","docs","redoc","openapi.json"]+[*postgres_object]:return function_http_response(400,0,f"allowed x={[*postgres_object]}")
   #api response
   if x in postgres_object:request.state.postgres_object=postgres_object[x]
   try:response=await api_function(request)
   except Exception as e:return function_http_response(400,0,e.args)
   #final response
   return response

#root
@app.get("/")
async def function_api_root():return {"status":1,"message":f"welcome to {[*postgres_object]}"}

#router
from api import router
app.include_router(router)

#server start
from function import function_server_start
if __name__=="__main__":function_server_start(app,"0.0.0.0",8000)
