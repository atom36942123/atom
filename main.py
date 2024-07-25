#env
from environs import Env
env=Env()
env.read_env()

#schema
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
class schema_database(BaseModel):
    id:int|None=None
    created_at:datetime|None=None
    created_by_id:int|None=None
    updated_at:datetime|None=None
    updated_by_id:int|None=None
    is_active:int|None=None
    is_verified:int|None=None
    parent_table:str|None=None
    parent_id:int|None=None
    received_by_id:int|None=None
    last_active_at:datetime|None=None
    firebase_id:str|None=None
    google_id:str|None=None
    otp:int|None=None
    metadata:dict|None=None
    username:str|None=None
    password:str|None=None
    profile_pic_url:str|None=None
    date_of_birth:datetime|None=None
    name:str|None=None
    gender:str|None=None
    email:str|None=None
    mobile:str|None=None
    whatsapp:str|None=None
    phone:str|None=None
    country:str|None=None
    state:str|None=None
    city:str|None=None
    type:str|None=None
    title:str|None=None
    description:str|None=None
    file_url:str|None=None
    link_url:str|None=None
    tag:list|None=None
    date:datetime|None=None
    status:str|None=None
    remark:str|None=None
    rating:float|None=None
    is_pinned:int|None=None
    work_type:str|None=None
    work_profile:str|None=None
    degree:str|None=None
    college:str|None=None
    linkedin_url:str|None=None
    portfolio_url:str|None=None
    experience:int|None=None
    experience_work_profile:int|None=None
    is_working:int|None=None
    location_current:str|None=None
    location_expected:str|None=None
    currency:str|None=None
    salary_frequency:str|None=None
    salary_current:int|None=None
    salary_expected:int|None=None
    sector:str|None=None
    past_company_count:int|None=None
    past_company_name:str|None=None
    marital_status:str|None=None
    physical_disability:str|None=None
    hobby:str|None=None
    language:str|None=None
    joining_days:int|None=None
    career_break_month:int|None=None
    resume_url:str|None=None
    achievement:str|None=None
    certificate:str|None=None
    project:str|None=None
    is_founder:int|None=None
    soft_skill:str|None=None
    tool:str|None=None
    achievement_work:str|None=None

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
   #assgin
   request.state.postgres_object=None
   request.state.schema_database=schema_database
   if x in postgres_object:request.state.postgres_object=postgres_object[x]
   #api response
   try:response=await api_function(request)
   except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
   #except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":traceback.format_exc()}))
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
