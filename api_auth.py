#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#singup
from fastapi import Request
import hashlib
@router.post("/{x}/auth/signup")
async def function_auth_signup(request:Request):
   #database
   postgres_object=request.state.postgres_object
   #body
   body=await request.json()
   username=body["username"]
   password=str(body["password"])
   #conversion
   password=hashlib.sha256(password.encode()).hexdigest()
   #qrunner
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param_dict={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param_dict)
   #final
   return {"status":1,"message":output}

#login
from fastapi import Request
import hashlib
from function import function_create_token
@router.post("/{x}/auth/login")
async def function_auth_login(request:Request):
   #database
   postgres_object=request.state.postgres_object
   #body
   body=await request.json()
   username=body["username"]
   password=str(body["password"])
   #conversion
   password=hashlib.sha256(password.encode()).hexdigest()
   #read user
   query="select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param_dict={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param_dict)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #create token
   response=await function_create_token(user,request,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#google
from fastapi import Request
import hashlib
from config import config_key_jwt
from function import function_create_token
@router.post("/{x}/auth/google")
async def function_auth_google(request:Request):
   #body
   body=await request.json()
   google_id=str(body["google_id"])
   #read user
   query="select * from users where google_id=:google_id order by id desc limit 1;"
   values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (google_id) values (:google_id) returning *;"
      values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
      output=await postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #create token
   response=await function_create_token(user,request,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#email
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from config import config_key_jwt
from function import function_create_token
@router.post("/{x}/auth/email")
async def function_auth_email(request:Request):
   #body
   body=await request.json()
   email=body["email"]
   otp=body["otp"]
   #verify otp
   query="select otp from otp where email=:email order by id desc limit 1;"
   values={"email":email}
   output=await postgres_object.fetch_all(query=query,values=values)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
   #read user
   query="select * from users where email=:email order by id desc limit 1;"
   values={"email":email}
   output=await postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (email) values (:email) returning *;"
      values={"email":email}
      output=await postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #create token
   response=await function_create_token(user,request,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from config import config_key_jwt
from function import function_create_token
@router.post("/{x}/auth/mobile")
async def function_auth_mobile(request:Request):
   #body
   body=await request.json()
   mobile=body["mobile"]
   otp=body["otp"]
   #verify otp
   query="select otp from otp where mobile=:mobile order by id desc limit 1;"
   values={"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=values)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
   #read user
   query="select * from users where mobile=:mobile order by id desc limit 1;"
   values={"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (mobile) values (:mobile) returning *;"
      values={"mobile":mobile}
      output=await postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #create token
   response=await function_create_token(user,request,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}

#refresh
from fastapi import Request
import jwt,json
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from config import config_key_jwt
from function import function_create_token
@router.get("/{x}/auth/refresh")
async def function_auth_refresh(request:Request):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #create token
   response=await function_create_token(user,request,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   token=response["message"]
   #final
   return {"status":1,"message":token}
