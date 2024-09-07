#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#common
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_auth_check
from fastapi import BackgroundTasks
from fastapi_cache.decorator import cache
from function import function_redis_key_builder
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
from function import function_add_creator_key
from function import function_add_action_count

#auth
import hashlib
from function import function_token_create
@router.post("/auth/signup-username",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_auth_signup_username(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=hashlib.sha256(str(request_body["password"]).encode()).hexdigest()
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

import hashlib
from function import function_token_create
@router.post("/auth/login-password")
async def function_auth_login_password(request:Request):
   #request body
   request_body=await request.json()
   password=hashlib.sha256(str(request_body["password"]).encode()).hexdigest()
   request_body.pop("password")
   for k,v in request_body.items():
      if k not in ["username","email","mobile"]:return JSONResponse(status_code=400,content={"status":0,"message":"column not allowed"})
      column,value=k,v
   #read user
   query=f"select * from users where {column}=:value and password=:password order by id desc limit 1;"
   query_param={"value":value,"password":password}
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
@router.post("/auth/login-oauth")
async def function_auth_login_oauth(request:Request):
   #request body
   request_body=await request.json()
   for k,v in request_body.items():
      if k not in ["google_id"]:return JSONResponse(status_code=400,content={"status":0,"message":"oauth column not allowed"})
      column,value=k,hashlib.sha256(v.encode()).hexdigest()
   #read user force
   response=await function_read_user_force(postgres_object,column,value)
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
@router.post("/auth/login-otp")
async def function_auth_login_otp(request:Request):
   #request body
   request_body=await request.json()
   otp=request_body["otp"]
   if "email" in request_body:email,mobile=request_body["email"],None
   else:email,mobile=None,request_body["mobile"]
   if email:column,value="email",email
   else:column,value="mobile",mobile
   #otp verify
   response=await function_otp_verify(postgres_object,otp,email,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user force
   response=await function_read_user_force(postgres_object,column,value)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my
from datetime import datetime
from function import function_object_update
@router.get("/my/profile")
async def function_my_profile(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),"updated_by_id":user["id"]}
   response=await function_object_update(postgres_object,"background","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":user}

from function import function_query_dict_runner
@router.get("/my/metric")
async def function_my_metric(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query_dict={ "post_count":f"select count(*) from post where created_by_id={user['id']};","message_unread_count":f"select count(*) from message where parent_table='users' and parent_id={user['id']} and status is null;"}
   response=await function_query_dict_runner(postgres_object,query_dict)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_token_create
@router.get("/my/token-refresh")
async def function_my_token_refresh(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user exist for token passed"})
   #token create
   response=await function_token_create(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

@router.delete("/my/delete-account")
async def function_my_delete_account(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #delete object
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

from function import function_object_create
@router.post("/my/object-create")
async def function_my_object_create(request:Request,table:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   object["created_by_id"]=user["id"]
   [object.pop(item) for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"] if item in object]
   response=await function_object_create(postgres_object,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_ownership_check
from function import function_object_update
@router.put("/my/object-update")
async def function_my_object_update(request:Request,table:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #body
   object=await request.json()
   #object ownership check
   response=await function_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   object["updated_by_id"]=user["id"]
   [object.pop(item) for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"] if item in object]
   response=await function_object_update(postgres_object,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_raw
@router.get("/my/object-read")
async def function_my_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #where raw
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}|{"created_by_id":f"=,{user['id']}"}
   response=await function_where_raw(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

from function import function_where_raw
@router.delete("/my/object-delete")
async def function_my_object_delete(request:Request,table:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #where raw
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table"]}|{"created_by_id":f"=,{user['id']}"}
   response=await function_where_raw(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   query=f"delete from {table} {where_string};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

@router.delete("/my/bulk-ids-delete")
async def function_my_bulk_ids_delete(request:Request,table:str,ids:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids)>100:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   query=f"delete from {table} where id in ({ids}) and created_by_id=:created_by_id;"
   query_param={"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#parent read
from function import function_parent_read
@router.get("/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_parent_read(postgres_object,table,parent_table,user["id"],"id desc",limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#parent check
from function import function_parent_check
@router.get("/my/parent-check")
async def function_my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_parent_check(postgres_object,table,parent_table,parent_ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

from datetime import datetime
from function import function_message_read
from function import function_object_update
@router.get("/my/message-read")
async def function_my_message_read(request:Request,background:BackgroundTasks,mode:str,order:str="id desc",limit:int=100,page:int=1,user_id:int=None):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_message_read(postgres_object,"users",mode,user["id"],user_id,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #background
   if mode=="thread":
      query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"parent_id":user["id"]}
      background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   if mode in ["received","received_unread"]:
      object_list=[]
      for item in output:
         object={"id":item["id"],"status":"read","updated_by_id":user["id"]}
         object_list.append(object)
      response=await function_object_update(postgres_object,"background","message",object_list)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

from function import function_message_delete
@router.delete("/my/message-delete")
async def function_my_message_delete(request:Request,mode:str,id:int=None):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_message_delete(postgres_object,"users",mode,user["id"],id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public
@router.get("/public/project-cache")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_public_project_cache(request:Request):
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   response=await function_query_dict_runner(postgres_object,query_dict)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_raw
@router.get("/public/object-read")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_public_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #where raw
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_where_raw(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add action count
   response=await function_add_action_count(postgres_object,output,table,"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

@router.get("/public/bulk-ids-read")
async def function_public_bulk_ids_read(request:Request,table:str,ids:str):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

from function import function_where_raw
from function import function_search_location
@router.get("/public/search-location")
async def function_public_search_location(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #where raw
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","location","within","order","limit","page"]}
   response=await function_where_raw(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   response=await function_search_location(postgres_object,table,where_string,where_param,location,within,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin
from function import function_database_init
@router.get("/admin/database-init")
async def function_admin_database_init(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"root",request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   response=await function_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
   
@router.get("/admin/query-runner")
async def function_admin_query_runner(request:Request,mode:str,query:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
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
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
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
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
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

from function import function_object_update
@router.put("/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   request_body=await request.json()
   table,id,column,value=request_body["table"],request_body["id"],request_body["column"],request_body["value"]
   object={"id":id,column:value,"updated_by_id":user["id"]}
   response=await function_object_update(postgres_object,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_raw
@router.get("/admin/object-read")
async def function_admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
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

@router.get("/admin/bulk-ids-read")
async def function_admin_bulk_ids_read(request:Request,table:str,ids:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

@router.delete("/admin/bulk-ids-delete")
async def function_admin_bulk_ids_delete(request:Request,table:str,ids:str):
   #auth
   response=await function_auth_check(postgres_object,"jwt",request,["admin"])
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

#external
from function import function_aws
@router.post("/external/aws")
async def function_external_aws(request:Request):
   #request body
   payload=await request.json()
   mode=payload["mode"]
   payload.pop("mode")
   #auth
   if "delete" in mode:
      response=await function_auth_check(postgres_object,"jwt",request,["admin"])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
   response=await function_aws(mode,payload)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
