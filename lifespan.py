#import
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from object import redis_object
from object import postgres_object

#logic
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
   #postgres disconnect
   yield
   for k,v in postgres_object.items():
      try:await v.disconnect()
      except Exception as e:print(e.args)
