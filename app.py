#app
from fastapi import FastAPI
from lifespan import lifespan
app=FastAPI(lifespan=lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from config import config_x
from function import function_http_response
@app.middleware("http")
async def middleware(request:Request,api_function):
   #x check
   if str(request.url).split("/")[3] not in ["","docs","redoc","openapi.json"]+config_x:return function_http_response(400,0,f"allowed x={str(config_x)}")
   #api response
   try:response=await api_function(request)
   except Exception as e:return function_http_response(400,0,e.args)
   #finally
   return response

#router
from api import router_database
app.include_router(router_database)
