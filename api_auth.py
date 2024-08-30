#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#singup
from fastapi import Request
from config import postgres_object
import hashlib
from function import function_token_create
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_auth_signup(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=str(request_body["password"])
   password=hashlib.sha256(password.encode()).hexdigest()
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #read user
   user_id=output[0]["id"]
   query="select * from users where id=:id;"
   query_param={"id":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
import hashlib
from function import function_token_create
@router.post("/auth/login")
async def function_auth_login(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=str(request_body["password"])
   password=hashlib.sha256(password.encode()).hexdigest()
   #read user
   query="select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#google
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
import hashlib
from function import function_token_create
from function import function_read_user_force
@router.post("/auth/google")
async def function_auth_google(request:Request):
   #request body
   request_body=await request.json()
   google_id=str(request_body["google_id"])
   google_id=hashlib.sha256(google_id.encode()).hexdigest()
   #read user force
   response=await function_read_user_force(postgres_object,"google_id",google_id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#email
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_otp_verify
from function import function_token_create
from function import function_read_user_force
@router.post("/auth/email")
async def function_auth_email(request:Request):
   #request body
   request_body=await request.json()
   email=request_body["email"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,"email",email,otp)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user force
   response=await function_read_user_force(postgres_object,"email",email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_otp_verify
from function import function_token_create
from function import function_read_user_force
@router.post("/auth/mobile")
async def function_auth_mobile(request:Request):
   #request body
   request_body=await request.json()
   mobile=request_body["mobile"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,"mobile",mobile,otp)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user force
   response=await function_read_user_force(postgres_object,"mobile",mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}
