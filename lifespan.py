#import
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

#logic
@asynccontextmanager
async def lifespan(app:FastAPI):
   #redis
   config_redis_url="redis://127.0.0.1"
   await FastAPILimiter.init(aioredis.from_url(config_redis_url,encoding="utf-8",decode_responses=True))
   FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_url)))
   #postgres
   for k,v in postgres_object.items():await v.connect()
   #shutdown
   yield
   for k,v in postgres_object.items():await v.disconnect()
