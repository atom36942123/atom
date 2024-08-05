#app
from fastapi import FastAPI
from lifespan import function_lifespan
app=FastAPI(lifespan=function_lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback
from config import config_postgres_object
@app.middleware("http")
async def middleware(request:Request,api_function):
  #x check
  key_4th=str(request.url.path).split("/")[1]
  if key_4th not in ["","docs","redoc","openapi.json"]+[*config_postgres_object]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
  #postgres object assgin
  if key_4th in config_postgres_object:request.state.postgres_object=postgres_object[key_4th]
  #api response
  try:response=await api_function(request)
  except Exception as e:
    print(traceback.format_exc())
    return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
  #final
  return response
