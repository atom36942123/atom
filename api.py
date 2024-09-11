#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#database init
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_postgres_object
from function import function_auth_check
from config import config_key_root,config_key_jwt
from function import function_postgres_database_init
@router.get("/utility/database-init")
async def function_database_init(request:Request):
   #auth
   response=await function_auth_check("root",request,config_key_root,config_key_jwt,config_postgres_object,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_postgres_database_init(config_postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_postgres_object
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
import hashlib
from function import function_token_create
from config import config_key_jwt
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_signup(request:Request,username:str,password:str):
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await config_postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await function_token_create(user,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_postgres_object
from function import function_postgres_read_user_force
from function import function_postgtes_otp_verify
from function import function_token_create
from config import config_key_jwt
@router.post("/auth/login")
async def function_login(request:Request,mode:str,username:str=None,password:str=None,google_id:str=None,otp:int=None,email:str=None,mobile:str=None,type:str=None):
   #logic
   if mode=="username_password":
      query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
      query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
      output=await config_postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="oauth_google":
      response=await function_postgres_read_user_force(config_postgres_object,"google_id",google_id)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_email":
      response=await function_postgres_otp_verify(config_postgres_object,otp,email,None)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_postgres_read_user_force(config_postgres_object,"email",email)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_mobile":
      response=await function_postgres_otp_verify(config_postgres_object,otp,None,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_postgres_read_user_force(config_postgres_object,"mobile",mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   #user type check
   if type and user["type"]!=type:return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await function_token_create(user,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#profile
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_postgres_object
from function import function_auth_check
from config import config_key_root,config_key_jwt
@router.get("/my/profile")
async def function_profile(request:Request):
   #auth
   response=await function_auth_check("jwt",request,config_key_root,config_key_jwt,config_postgres_object,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await config_postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   object={"id":user["id"],"updated_by_id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   response=await function_object_update(postgres_object,"background","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":user}
