#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#common
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_auth_check
from config import config_key_root

#auth
import hashlib
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
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
   query="select * from users where id=:id;"
   query_param={"id":output[0]["id"]}
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
@router.post("/auth/oauth")
async def function_auth_oauth(request:Request):
   #request body
   request_body=await request.json()
   if len(request_body)!=1:return JSONResponse(status_code=400,content={"status":0,"message":"body key length should be 1"})
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
@router.post("/auth/otp")
async def function_auth_otp(request:Request):
   #request body
   request_body=await request.json()
   if len(request_body)!=2:return JSONResponse(status_code=400,content={"status":0,"message":"body key length should be 1"})
   otp=request_body["otp"]
   if "email" in request_body:
      email,mobile=request_body["email"],None
      column,value="email",email
   else:
      email,mobile=None,request_body["mobile"]
      column,value="mobile",mobile
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
from function import function_update_last_active_at
@router.get("/my/profile")
async def function_my_profile(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   response=await function_update_last_active_at(postgres_object,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":user}

from function import function_query_dict_runner
@router.get("/my/metric")
async def function_my_metric(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query_dict={ "post_count":f"select count(*) as x from post where created_by_id={user['id']};","message_unread_count":f"select count(*) as x from message where parent_table='users' and parent_id={user['id']} and status is null;"}
   response=await function_query_dict_runner(postgres_object,query_dict)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_token_create
@router.get("/my/token-refresh")
async def function_my_token_refresh(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   object["created_by_id"]=user["id"]
   [object.pop(item) for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"] if item in object]
   response=await function_object_create(postgres_object,table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_ownership_check
from function import function_object_update
@router.put("/my/object-update")
async def function_my_object_update(request:Request,table:str):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   response=await function_object_update(postgres_object,table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_raw
@router.get("/my/object-read")
async def function_my_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
from function import function_add_creator_key
@router.get("/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
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
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_parent_check(postgres_object,table,parent_table,parent_ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

from function import function_add_creator_key
from function import function_mark_message_object_read
@router.get("/my/message-received")
async def function_my_message_received(request:Request,mode:str=None,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   if mode=="unread":query=f"select * from message where parent_table='users' and parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #mark message object read
   response=await function_mark_message_object_read(postgres_object,output,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

@router.delete("/my/message-delete")
async def function_my_message_delete(request:Request,mode:str,id:int=None):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="created":
      query="delete from message where parent_table='users' and created_by_id=:created_by_id;"
      query_param={"created_by_id":user['id']}
   if mode=="received":
      query="delete from message where parent_table='users' and parent_id=:parent_id;"
      query_param={"parent_id":user['id']}
   if mode=="all":
      query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
      query_param={"created_by_id":user['id'],"parent_id":user['id']}
   if mode=="single":
      query="delete from message where parent_table='users' and id=:id and (created_by_id=:created_by_id or parent_id=:parent_id);"
      query_param={"id":id,"created_by_id":user['id'],"parent_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

@router.get("/my/message-inbox")
async def function_my_message_inbox(request:Request,mode:str=None,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   if mode=="unread":query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/my/message-thread")
async def function_my_message_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #mark message read
   query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"parent_id":user["id"]}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}

#public
from fastapi_cache.decorator import cache
from function import function_query_dict_runner
@router.get("/public/project-cache")
@cache(expire=60)
async def function_public_project_cache(request:Request):
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   response=await function_query_dict_runner(postgres_object,query_dict)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from fastapi_cache.decorator import cache
from function import function_redis_key_builder
from function import function_where_raw
from function import function_add_creator_key
from function import function_add_action_count
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
   #auth check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #logic
   response=await function_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
   
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

@router.get("/admin/bulk-ids-read")
async def function_admin_bulk_ids_read(request:Request,table:str,ids:str):
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

@router.delete("/admin/bulk-ids-delete")
async def function_admin_bulk_ids_delete(request:Request,table:str,ids:str):
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

#external
from function import function_aws
@router.get("/external/s3-create-presigned-url")
async def function_external_s3_create_presigned_url(request:Request,filename:str):
   #logic
   response=await function_aws("s3_create_presigned_url",{"filename":filename})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_aws
@router.post("/external/ses-send-email")
async def function_external_ses_send_email(request:Request):
   #logic
   body=await request.json()
   response=await function_aws("ses_send_email",body)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_aws
@router.delete("/external/s3-delete-single")
async def function_external_s3_delete_single(request:Request,url:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_aws("s3_delete_single",{"url":url})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_aws
@router.delete("/external/s3-delete-all")
async def function_external_s3_delete_all(request:Request):
   #auth check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #logic
   response=await function_aws("s3_delete_all",{})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
