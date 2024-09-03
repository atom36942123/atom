#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#common
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_auth_check

#rate limiter
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends

#auth
import hashlib
from function import function_token_create
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

from function import function_otp_verify
from function import function_read_user_force
from function import function_token_create
@router.post("/auth/email")
async def function_auth_email(request:Request):
   #request body
   request_body=await request.json()
   email=request_body["email"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,otp,email,None)
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

from function import function_otp_verify
from function import function_read_user_force
from function import function_token_create
@router.post("/auth/mobile")
async def function_auth_mobile(request:Request):
   #request body
   request_body=await request.json()
   mobile=request_body["mobile"]
   otp=request_body["otp"]
   #otp verify
   response=await function_otp_verify(postgres_object,otp,None,mobile)
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

#admin
@router.get("/admin/query-runner")
async def function_admin_query_runner(request:Request,mode:str,query:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
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

from function import function_database_clean
@router.delete("/admin/database-clean")
async def function_admin_database_clean(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_database_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from fastapi import UploadFile
from function import function_file_to_object_list
from function import function_object_create
from function import function_object_update
@router.post("/admin/csv")
async def function_admin_csv(request:Request,mode:str,table:str,file:UploadFile):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await function_file_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   if mode=="create":response=await function_object_create(postgres_object,table,object_list)
   if mode=="update":response=await function_object_update(postgres_object,table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_object_update
@router.put("/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   request_body=await request.json()
   table,id,column,value=request_body["table"],request_body["id"],request_body["column"],request_body["value"]
   object={"id":id,column:value,"updated_by_id":user["id"]}
   response=await function_object_update(postgres_object,table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_raw
@router.get("/admin/object-read")
async def function_admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #where raw
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_where_raw(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

@router.get("/admin/bulk-read")
async def function_admin_bulk_read(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

@router.delete("/admin/bulk-delete")
async def function_admin_bulk_delete(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids)>100:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
