#import
from object import postgres_object
from config import *
from function import *
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal
import json
import random
import uuid
from fastapi import File
from fastapi import UploadFile
from fastapi import Body
from fastapi_cache.decorator import cache

#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#api
@router.get("/{x}/create-s3-url")
async def api_func(x:str,request:Request,filename:str,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    key=str(uuid.uuid4())+"."+filename.split(".")[-1]
    response=await function_s3_create_url(config_aws_s3_bucket_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #save s3 url
    query="insert into s3 (created_by_id,file_url) values (:created_by_id,:file_url) returning *;"
    values={"created_by_id":request_user["id"],"file_url":response["message"]['url']+response["message"]['fields']['key']}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.delete("/{x}/delete-s3-url")
async def api_func(x:str,request:Request,url:str,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #admin check
    if request_user["is_admin"]!=1:return function_http_response(400,0,"only admin allowed")
    if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
    #logic
    response=await function_s3_delete_url(config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,url)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #delete saved url
    query="delete from s3 where file_url=:file_url;"
    values={"file_url":url}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response




