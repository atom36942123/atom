#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#import
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from fastapi_cache.decorator import cache
from function import function_redis_key_builder
from function import function_postgres_add_creator_key
from function import function_postgres_add_action_count
from function import function_auth
from config import config_key_root,config_key_jwt,postgres_object

#auth
import hashlib
from function import function_token_create
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_auth_signup(request:Request,username:str,password:str):
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

import hashlib
from function import function_token_create
from function import function_read_user_force
from function import function_otp_verify
@router.post("/auth/login")
async def function_auth_login(request:Request,mode:str,username:str=None,password:str=None,google_id:str=None,otp:int=None,email:str=None,mobile:str=None,type:str=None):
   #logic
   if mode=="username_password":
      query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
      query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="oauth_google":
      response=await function_read_user_force(postgres_object,"google_id",google_id)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_email":
      response=await function_otp_verify(postgres_object,otp,email,None)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_read_user_force(postgres_object,"email",email)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_mobile":
      response=await function_otp_verify(postgres_object,otp,None,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_read_user_force(postgres_object,"mobile",mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   #user type check
   if type and user["type"]!=type:return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}
