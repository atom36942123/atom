#import
from postgres import postgres_object_dict
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback

#logic
@app.middleware("http")
async def middleware(request:Request,api_function):
  #url split (4th position)
  key_4th=str(request.url.path).split("/")[1]
  #x check
  if key_4th not in ["","docs","openapi.json","redoc"]+[*postgres_object_dict]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in postgres_object_dict:request.state.postgres_object=postgres_object_dict[key_4th]
  #api response
  try:response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response

