#import
from config import config_redis_server_uri
from config
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

#logic
@asynccontextmanager
async def function_lifespan(app:FastAPI):
  #redis cache
  FastAPICache.init(RedisBackend(aioredis.from_url(config_redis_server_uri)))
  #redis rate limiter
  await FastAPILimiter.init(aioredis.from_url(config_redis_server_uri,encoding="utf-8",decode_responses=True))
  #postgres connect
  for k,v in postgres_object_dict.items():await v.connect()
  #shutdown
  yield
  #postgres disconnect
  for k,v in postgres_object_dict.items():await v.disconnect()
