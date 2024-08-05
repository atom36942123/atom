#config
from config import config_redis_url
from config import config_postgres_object

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  #redis cache
  FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_url)))
  #redis rate limiter
   await FastAPILimiter.init(aioredis.from_url(config_redis_url,encoding="utf-8",decode_responses=True))
   #postgres connect
   for k,v in config_postgres_object.items():await v.connect()
   #shutdown
   yield
   #postgres disconnect
   for k,v in config_postgres_object.items():await v.disconnect()

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
   #postgres object assgin
   key_4th=str(request.url.path).split("/")[1]
   if key_4th in config_postgres_object:request.state.postgres_object=postgres_object[key_4th]
   #api response
   try:response=await api_function(request)
   except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
   #except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":traceback.format_exc()}))
   #final
   return response

#root api
@app.get("/")
async def function_root():
   return {"status":1,"message":f"welcome to {[*config_postgres_object]}"}

#server start
import uvicorn,asyncio
if __name__=="__main__":
  uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
  loop=asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(uvicorn_object.serve())

