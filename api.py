#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#database
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_postgres_database_init
@router.get("/database")
async def function_database(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   #logic
   response=await function_postgres_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import function_token_create
from config import config_jwt_secret_key
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
@router.post("/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_signup(request:Request,username:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await function_token_create(user,config_jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import function_token_create
from config import config_jwt_secret_key
from function import function_postgres_read_user_force
from function import function_postgtes_otp_verify
@router.post("/login")
async def function_login(request:Request,mode:str,username:str=None,password:str=None,google_id:str=None,otp:int=None,email:str=None,mobile:str=None,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   #logic
   if mode=="username_password":
      query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
      query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="oauth_google":
      response=await function_postgres_read_user_force(postgres_object,"google_id",google_id)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_email":
      response=await function_postgres_otp_verify(postgres_object,otp,email,None)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_postgres_read_user_force(postgres_object,"email",email)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_mobile":
      response=await function_postgres_otp_verify(postgres_object,otp,None,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await function_postgres_read_user_force(postgres_object,"mobile",mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   #user type check
   if type and user["type"]!=type:return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await function_token_create(user,config_jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#profile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import config_jwt_secret_key
from datetime import datetime
from function import function_postgres_object_update
@router.get("/profile")
async def function_profile(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await function_auth_check(request,config_jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   response=await function_postgres_object_update(postgres_object,column_datatype,"background","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":user}

#token refresh
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import config_jwt_secret_key
from function import function_token_create
@router.get("/token")
async def function_token(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   #auth check
   response=await function_auth_check(request,config_jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user exist for token passed"})
   #token create
   response=await function_token_create(user,config_jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#exit
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import config_jwt_secret_key
@router.delete("/exit")
async def function_exit(request:Request):
   #auth check
   response=await function_auth_check(request,config_jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #permisson check
   if True:return {"status":1,"message":"exit not allowed"}
   #logic
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"account deleted"}

#csv
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import config_jwt_secret_key
from fastapi import UploadFile
from function import function_file_to_object_list
from function import function_object_create
from function import function_object_update
@router.post("/utility/csv")
async def function_utility_csv(request:Request,mode:str,table:str,file:UploadFile):
   #auth
   response=await function_auth("jwt",request,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await function_file_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   if mode=="create":response=await function_object_create(postgres_object,"normal",table,object_list)
   if mode=="update":response=await function_object_update(postgres_object,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
