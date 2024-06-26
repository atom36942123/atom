#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
import hashlib
from pydantic import BaseModel
from typing import Literal

#router
from fastapi import APIRouter
router=APIRouter(tags=["login"])

#schema
class schema_signup(BaseModel):
   username:str
   password:str
   
class schema_login(BaseModel):
   mode:Literal["username","firebase","email","mobile"]="username"
   username:str|None=None
   password:str|None=None
   firebase_id:str|None=None
   email:str|None=None
   mobile:str|None=None
   otp:int|None=None

#api
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_api_signup(x:str,request:Request,body:schema_signup):
   #check body
   response=await function_check_body(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #check username if exist
   query="select * from users where username=:username;"
   values={"username":body.username}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if response["message"]:return function_http_response(400,0,"username already exist")
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.post("/{x}/login")
async def function_api_login(x:str,request:Request,body:schema_login):
   #check mode
   if body.mode=="username":
      if not body.username or not body.password:return function_http_response(400,0,"username/password must")
      body.firebase_id,body.email,body.mobile=None,None,None
   if body.mode=="firebase":
      if not body.firebase:return function_http_response(400,0,"firebase_id must")
      body.username,body.password,body.email,body.mobile=None,None,None,None
   if body.mode=="email":
      if not body.email or not body.otp:return function_http_response(400,0,"email must")
      body.username,body.password,body.firebase_id,body.mobile=None,None,None,None
   if body.mode=="mobile":
      if not body.mobile or not body.otp:return function_http_response(400,0,"mobile must")
      body.username,body.password,body.firebase_id,body.email=None,None,None,None
   #check body
   response=await function_check_body(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #verify otp
   if body.mode in ["email","mobile"]:
      param={"email":body.email,"mobile":body.mobile}
      response=await function_object_read(postgres_object[x],function_query_runner,"otp",param,["id","desc",1,0])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
   #read user
   param={"username":body.username,"password":body.password,"firebase_id":body.firebase_id,"email":body.email,"mobile":body.mobile}
   response=await function_object_read(postgres_object[x],function_query_runner,"users",param,["id","desc",1,0])
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:user=None
   else:user=response["message"][0]
   #check user
   if body.mode=="username" and not user:return function_http_response(400,0,"no such user")
   if body.mode in ["firebase","email","mobile"] and not user:
      #create user
      query="insert into users (firebase_id,email,mobile) values (:firebase_id,:email,:mobile) returning *;"
      values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest(),"email":body.email,"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"write",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #read user
      param={"id":response["message"]}
      response=await function_object_read(postgres_object[x],function_query_runner,"users",param,["id","desc",1,0])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/token-refresh")
async def function_api_token_refresh(x:str,request:Request):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #read user
   query="select * from users where id=:id;"
   values={"id":request_user["id"]}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response
