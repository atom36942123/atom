#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from object import redis_object
from object import postgres_object
@asynccontextmanager
async def lifespan(app:FastAPI):
   #redis cache
   try:FastAPICache.init(RedisBackend(redis_object))
   except Exception as e:print(e.args)
   #rate limiter
   try:await FastAPILimiter.init(redis_object)
   except Exception as e:print(e.args)
   #postgres connect
   for k,v in postgres_object.items():
      try:await v.connect()
      except Exception as e:print(e.args)
   yield
   #postgres disconnect
   for k,v in postgres_object.items():
      try:await v.disconnect()
      except Exception as e:print(e.args)

#app
app=FastAPI(lifespan=lifespan)

#middleware
from fastapi import Request
from config import config_x
from function import function_http_response
@app.middleware("http")
async def middleware(request:Request,api_function):
   #x check
   if str(request.url).split("/")[3] not in ["","docs","redoc","openapi.json"]+config_x:return function_http_response(400,0,"wrong x")
   #api response
   try:response=await api_function(request)
   except Exception as e:return e.args
   #finally
   return response

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#api
@app.get("/")
async def api_func_root():
   return {"status":1,"message":"welcome to atom"}

@app.get("/{x}")
async def api_func_root(x:str):
   return {"status":1,"message":f"welcome to {x}"}

#router
from api_database import router
app.include_router(router)
from api_login import router
app.include_router(router)
from api_my import router
app.include_router(router)
from api_crud import router
app.include_router(router)
from api_utility import router
app.include_router(router)
from api_admin import router
app.include_router(router)
from api_zzz import router
app.include_router(router)

#server
from config import config_backend_host
from config import config_backend_port
from function import function_server_start
if __name__=="__main__":
   function_server_start(app,config_backend_host,config_backend_port)

