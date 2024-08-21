#sentry
from config import config_sentry_dsn
import sentry_sdk
if False:
  sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#app
from lifespan import function_lifespan
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from app import app
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
  CORSMiddleware,allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],allow_headers=["*"]
)

#app import
from middleware import *
from router import *

#root api
from postgres import postgres_object_dict
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
   x_list=[*postgres_object_dict]
   return {"status":1,"message":f"welcome to {x_list}"}
