#sentry
from config import config_sentry_dsn
import sentry_sdk
if False:
  sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#app
from lifespan import function_lifespan
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#app import
from cors import *
from middleware import *

#root api
@app.get("/")
async def function_root():
   return {"status":1,"message":f"welcome to {[*postgres_object_dict]}"}
  
#router
from database import router as router_database
app.include_router(router_database)

from auth import router as router_auth
app.include_router(router_auth)

from my import router as router_my
app.include_router(router_my)

from object import router as router_object
app.include_router(router_object)

from action import router as router_action
app.include_router(router_action)

from message import router as router_message
app.include_router(router_message)

from utility import router as router_utility
app.include_router(router_utility)

from admin import router as router_admin
app.include_router(router_admin)

from feed import router as router_feed
app.include_router(router_feed)

from csvv import router as router_csv
app.include_router(router_csv)

from aws import router as router_aws
app.include_router(router_aws)

from mongo import router as router_mongo
app.include_router(router_mongo)

from elastic import router as router_elasticsearch
app.include_router(router_elasticsearch)
