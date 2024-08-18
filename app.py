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
from router import *
