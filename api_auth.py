#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#singup
from fastapi import Request
from config import postgres_object
import hashlib
@router.post("/auth/signup")
async def function_auth_signup(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=str(request_body["password"])
   #conversion
   password=hashlib.sha256(password.encode()).hexdigest()
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#login
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
import hashlib
from function import function_token_create_jwt
@router.post("/auth/login")
async def function_auth_login(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=str(request_body["password"])
   #conversion
   password=hashlib.sha256(password.encode()).hexdigest()
   #read user
   query="select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #raise error
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #token create
   response=await function_token_create_jwt(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#google
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
import hashlib
from function import function_token_create_jwt
@router.post("/auth/google")
async def function_auth_google(request:Request):
   #request body
   request_body=await request.json()
   google_id=str(request_body["google_id"])
   #conversion
   google_id=hashlib.sha256(google_id.encode()).hexdigest()
   #read user
   query="select * from users where google_id=:google_id order by id desc limit 1;"
   query_param={"google_id":google_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (google_id) values (:google_id) returning *;"
      query_param={"google_id":google_id}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      query_param={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0]
   #token create
   response=await function_token_create_jwt(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#email
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_otp_verify
from function import function_token_create_jwt
@router.post("/auth/email")
async def function_auth_email(request:Request):
   #request body
   request_body=await request.json()
   email=request_body["email"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,"email",email,otp)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user
   query="select * from users where email=:email order by id desc limit 1;"
   query_param={"email":email}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (email) values (:email) returning *;"
      query_param={"email":email}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      query_param={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0]
   #token create
   response=await function_token_create_jwt(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#mobile
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_otp_verify
from function import function_token_create_jwt
@router.post("/auth/mobile")
async def function_auth_mobile(request:Request):
   #request body
   request_body=await request.json()
   mobile=request_body["mobile"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,"mobile",mobile,otp)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user
   query="select * from users where mobile=:mobile order by id desc limit 1;"
   query_param={"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (mobile) values (:mobile) returning *;"
      query_param={"mobile":mobile}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      query_param={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0]
   #token create
   response=await function_token_create_jwt(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}
