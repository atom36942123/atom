#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#singup
from fastapi import Request
import hashlib
@router.post("/{x}/auth/signup")
async def function_auth_signup(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
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
import hashlib
from function import function_token_create
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/login")
async def function_auth_login(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
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
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #create token
   response=await function_token_create(request,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#google
from fastapi import Request
import hashlib
from function import function_token_create
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/google")
async def function_auth_google(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
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
   #create token
   response=await function_token_create(request,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#email
from fastapi import Request
from function import function_token_create
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/email")
async def function_auth_email(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #request body
   request_body=await request.json()
   email=request_body["email"]
   otp=request_body["otp"]
   #verify otp
   query="select otp from otp where email=:email order by id desc limit 1;"
   query_param={"email":email}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
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
   #create token
   response=await function_token_create(request,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#mobile
from fastapi import Request
from function import function_token_create
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/mobile")
async def function_auth_mobile(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #request body
   request_body=await request.json()
   mobile=request_body["mobile"]
   otp=request_body["otp"]
   #verify otp
   query="select otp from otp where mobile=:mobile order by id desc limit 1;"
   query_param={"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
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
   #create token
   response=await function_token_create(request,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#refresh
from fastapi import Request
from function import function_token_check
from function import function_token_create
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/auth/refresh")
async def function_auth_refresh(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #raise error
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #create token
   response=await function_token_create(request,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}
