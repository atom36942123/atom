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
   #param validaton
   response=await function_param_validation(vars(body))
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
   #param validation
   response=await function_param_validation(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #username
   if body.mode=="username":
      #check body
      if not body.username or not body.password:return function_http_response(400,0,"username/password must")
      #read user
      query="select * from users where username=:username and password=:password;"
      values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"no such user")
      #user define
      user=response["message"][0]
   #firebase
   if body.mode=="firebase":
      #check body
      if not body.firebase:return function_http_response(400,0,"firebase_id must")
      #read user
      query="select * from users where firebase_id=:firebase_id order by id desc limit 1;"
      values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (firebase_id) values (:firebase_id) returning *;"
         values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #email
   if body.mode=="email":
      #check body
      if not body.email or not body.otp:return function_http_response(400,0,"email is must")
      #otp check
      query="select * from otp where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (email) values (:email) returning *;"
         values={"email":body.email}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #mobile
   if body.mode=="mobile":
      if not body.mobile or not body.otp:return function_http_response(400,0,"mobile is must")
      query="select * from otp where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body.mobile}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
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
