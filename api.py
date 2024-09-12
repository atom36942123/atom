#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#database
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_init
from function import postgres_clean
@router.get("/database")
async def database(request:Request,mode:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   if mode=="init":response=await postgres_init(postgres_object)
   if mode=="clean":response=await postgres_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

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
from function import postgres_read_user_force
from function import postgtes_otp_verify
@router.post("/login")
async def login(request:Request,mode:str,username:str=None,password:str=None,google_id:str=None,otp:int=None,email:str=None,mobile:str=None,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   if mode=="username_password":
      query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
      query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="oauth_google":
      response=await postgres_read_user_force(postgres_object,"google_id",google_id)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_email":
      response=await postgres_otp_verify(postgres_object,otp,email,None)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await postgres_read_user_force(postgres_object,"email",email)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   if mode=="otp_mobile":
      response=await postgres_otp_verify(postgres_object,otp,None,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      response=await postgres_read_user_force(postgres_object,"mobile",mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   #user type check
   if type and user["type"]!=type:return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#my
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from datetime import datetime
from function import token_create
from function import postgres_object_update
@router.get("/my")
async def my(request:Request,mode:str,table:str=None,ids:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="profile":
      query="select * from users where id=:id;"
      query_param={"id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
      response={"status":1,"message":user}
   if mode=="token":
      query="select * from users where id=:id;"
      query_param={"id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
      response=await token_create(user,jwt_secret_key)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   if mode=="exit":
      if True:return {"status":1,"message":"exit not allowed"}
      query="delete from users where id=:id;"
      query_param={"id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      response={"status":1,"message":"account deleted"}
   if mode=="delete_ids":
      if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
      if len(ids.split(","))>3:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
      query=f"delete from {table} where created_by_id=:created_by_id and id in ({ids});"
      query_param={"created_by_id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      response={"status":1,"message":"ids deleted"}
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   await postgres_object_update(postgres_object,column_datatype,"background","users",[object])
   #final
   return response

#object create
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_create
@router.post("/object")
async def object_create(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","users","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   object["created_by_id"]=user["id"]
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import read_where_clause
@router.get("/object")
async def object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await read_where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#object update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_update
from function import postgres_object_ownership_check
@router.put("/object")
async def object_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   object["updated_by_id"]=user["id"]
   response=await postgres_object_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   if table=="users":
      for item in ["email","mobile"]:
         if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import read_where_clause
@router.delete("/object")
async def object_delete(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await read_where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"delete from {table} {where_string};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#csv
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_create
from function import postgres_object_update
@router.post("/csv")
async def csv(request:Request,mode:str,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   if mode=="create":response=await postgres_object_create(postgres_object,column_datatype,"normal",table,object_list)
   if mode=="update":response=await postgres_object_update(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#qrunner
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.get("/qrunner")
async def qrunner(request:Request,mode:str,query:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="single":
      query=query
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
   if mode=="bulk":
      for item in query.split("---"):
         query=item
         query_param={}
         output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#pcache
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from function import redis_key_builder
@router.get("/pcache")
@cache(expire=60,key_builder=redis_key_builder)
async def pcache(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   temp={}
   for k,v in query_dict.items():
      query=v
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

