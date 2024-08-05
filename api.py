#router
from fastapi import APIRouter
router = APIRouter()

#import
from fastapi import Request,Response,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs,jwt,time,boto3,uuid
from datetime import datetime,timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch

#api
@app.get("/{x}/qrunner")
async def function_qrunner(request:Request,query:str):
   #prework
   database=request.state.postgres_object.fetch_all
   if request.headers.get("token")!=config_key:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #logic
   query=query
   values={}
   output=await database(query=query,values=values)
   #final
   return output
