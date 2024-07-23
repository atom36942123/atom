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
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback
@app.middleware("http")
async def middleware(request:Request,api_function):
   #x check
   x=str(request.url).split("/")[3]
   if x not in ["","docs","redoc","openapi.json"]+[*postgres_object]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
   #database assgin
   request.state.postgres_object=None
   if x in postgres_object:request.state.postgres_object=postgres_object[x]
   #api response
   try:response=await api_function(request)
   except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
   # except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":traceback.format_exc()}))
   traceback.format_exc()

   #final response
   return response

#root
@app.get("/")
async def function_root():return {"status":1,"message":f"welcome to {[*postgres_object]}"}

#router
from api import router
app.include_router(router)

#server start
import uvicorn,asyncio
if __name__=="__main__":
   uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
   loop=asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(uvicorn_object.serve())
