#import
from postgres import postgres_object_dict
from config import config_key_root
from app import app
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback

#logic
@app.middleware("http")
async def function_middleware(request:Request,api_function):
  #key_4th
  key_4th=str(request.url.path).split("/")[1]
  #key_4th check
  key_4th_allowed_general=["","docs","openapi.json","redoc"]
  key_4th_allowed_postgres=[*postgres_object_dict]
  if key_4th not in key_4th_allowed_general+key_4th_allowed_postgres:
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in postgres_object_dict:
    request.state.postgres_object=postgres_object_dict[key_4th]
  #auth check root
  root_api=["database/qrunner"]
  path=str(request.url.path)
  token=request.headers.get("Authorization").split(" ",1)[1]
  for item in root_api:
    if item in path:
      if token!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token root issue"}))
  #api response
  try:
    response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response
