#package
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

#custom
from config import config_redis_url
from config import config_postgres_object

#logic
@asynccontextmanager
async def function_lifespan(app:FastAPI):
   #redis rate limiter
   await FastAPILimiter.init(aioredis.from_url(config_redis_url,encoding="utf-8",decode_responses=True))
   #redis cache
   FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_url)))
   #postgres connect
   for k,v in config_postgres_object.items():await v.connect()
   #shutdown
   yield
   #postgres disconnect
   for k,v in config_postgres_object.items():await v.disconnect()
