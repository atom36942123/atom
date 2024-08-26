#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#delete account
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.delete("/my/delete-account")
async def function_my_delete_account(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #delete object
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#profile
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_background_update_last_active_at
@router.get("/my/profile")
async def function_my_profile(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   response=await function_background_update_last_active_at(postgres_object,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":user}

#token refresh
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_token_create
@router.get("/my/token-refresh")
async def function_my_token_refresh(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
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
   token=response["message"]
   #final
   return {"status":1,"message":token}

#metric
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/my/metric")
async def function_my_metric(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   config_user_metric={
   "post_count":"select count(*) as x from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) as x from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   temp={}
   for k,v in config_user_metric.items():
      query=v
      query_param={"user_id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output[0]["x"]
   #final
   return {"status":1,"message":temp}

#object create
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_object_create
from function import function_sanitization
@router.post("/my/object-create")
async def function_my_object_create(request:Request,table:str):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #check
   if table in ["users","otp"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #logic
   payload=await request.json()
   payload["created_by_id"]=user_id
   response=await function_object_create(postgres_object,user["id"],table,payload,function_sanitization)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#object update
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_object_update
from function import function_sanitization
@router.put("/my/object-update")
async def function_my_object_update(request:Request,table:str,id:int):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   payload=await request.json()
   response=await function_object_update(postgres_object,user["id"],table,id,payload,function_sanitization)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#parent read
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/my/parent-read")
async def function_my_parent_read(request:Request,base_table:str,parent_table:str,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select parent_id from {base_table} where parent_table=:parent_table and created_by_id=:created_by_id order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   parent_ids_list=[item["parent_id"] for item in output]
   query=f"select * from {parent_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#parent check
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/my/parent-check")
async def function_my_parent_check(request:Request,base_table:str,parent_table:str,parent_ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   parent_ids_list=[int(item) for item in parent_ids.split(",")]
   query=f"select parent_id from {base_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   parent_ids_filtered=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":parent_ids_filtered}

#bulk
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/my/bulk")
async def function_my_bulk(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from {table} where created_by_id=:created_by_id and id in ({ids}) order by id desc;"
   query_param={"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
