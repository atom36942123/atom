#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
@router.post("/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def signup(request:Request,username:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
@router.get("/login")
async def login(request:Request,username:str,password:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login google
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgres_read_user_force
@router.get("/login-google")
async def login_google(request:Request,google_id:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_read_user_force(postgres_object,"google_id",google_id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login email
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.get("/login-email")
async def login_email(request:Request,email:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"email",email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login mobile
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.get("/login-mobile")
async def login_mobile(request:Request,mobile:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"mobile",mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}
