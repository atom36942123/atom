#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from function import redis_service_start
from config import redis_server_url
from function import postgres_column_datatype
@asynccontextmanager
async def lifespan(app:FastAPI):
  await redis_service_start(redis_server_url)
  await postgres_object.connect()
  global column_datatype
  response=await postgres_column_datatype(postgres_object)
  column_datatype=response["message"]
  yield
  await postgres_object.disconnect()
