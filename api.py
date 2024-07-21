#router
from fastapi import APIRouter
router=APIRouter()

#env
from environs import Env
env=Env()
env.read_env()

#import
from function import *
from fastapi import Request,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return function_http_response(400,0,"token issue")
   response=await request.state.postgres_object.execute(query=query,values={})
   return response

   
   
