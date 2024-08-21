#sentry
from config import config_sentry_dsn
import sentry_sdk
if False:
  sentry_sdk.init(dsn=config_sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#app
from function import function_lifespan
from fastapi import FastAPI
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from postgres import postgres_object_dict
from fastapi import Request
import traceback
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  #key_4th
  key_4th=str(request.url.path).split("/")[1]
  #key_4th check
  if key_4th not in ["","docs","openapi.json","redoc"]+[*postgres_object_dict]:
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in postgres_object_dict:
    request.state.postgres_object=postgres_object_dict[key_4th]
  #api response
  try:
    response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response

#app import
from router import *

#root api
from postgres import postgres_object_dict
from fastapi import Request
@app.get("/")
async def function_root(request:Request):
   return {"status":1,"message":f"welcome to {[*postgres_object_dict]}"}
