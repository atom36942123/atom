#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#profile
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_background_update_last_active_at
@router.get("/my/profile")
async def function_my_profile(request:Request):
   #auth check
   response=await function_token_check(postgres_object,request,None)
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

#delete account
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
@router.delete("/my/delete-account")
async def function_my_delete_account(request:Request):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #delete object
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#token refresh
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_token_create
@router.get("/my/token-refresh")
async def function_my_token_refresh(request:Request):
   #auth check
   response=await function_token_check(postgres_object,request,None)
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
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_metric_user
@router.get("/my/metric")
async def function_my_metric(request:Request):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_metric_user(postgres_object,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object create
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_object_create
@router.post("/my/object-create")
async def function_my_object_create(request:Request,table:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
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

#object update
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_token_check
from function import function_object_ownership_check
from function import function_object_update
@router.put("/my/object-update")
async def function_my_object_update(request:Request,table:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #body
   object=await request.json()
   #object ownership check
   response=await function_object_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   object["updated_by_id"]=user["id"]
   [object.pop(item) for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"] if item in object]
   response=await function_object_update(postgres_object,table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_token_check
from config import postgres_object
from function import function_object_read
@router.get("/my/object-read")
async def function_my_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}|{"created_by_id":f"=,{user['id']}"}
   response=await function_object_read(postgres_object,table,where_param_raw,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#bulk
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_token_check
from config import postgres_object
from function import function_bulk
@router.get("/my/bulk")
async def function_my_bulk(request:Request,mode:str,table:str,ids:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_bulk(postgres_object,mode,table,ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#parent read
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_parent_read
from function import function_add_creator_key
@router.get("/my/parent-read")
async def function_my_parent_read(request:Request,base_table:str,parent_table:str,limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_parent_read(postgres_object,base_table,parent_table,user["id"],"id desc",limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#parent check
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_parent_check
@router.get("/my/parent-check")
async def function_my_parent_check(request:Request,base_table:str,parent_table:str,parent_ids:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_parent_check(postgres_object,base_table,parent_table,parent_ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#parent delete
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
@router.delete("/my/parent-delete")
async def function_my_parent_delete(request:Request,base_table:str,parent_table:str,parent_ids:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"delete from {base_table} where parent_table=:parent_table and created_by_id=:created_by_id and parent_id in ({parent_ids});"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message received
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from function import function_add_creator_key
@router.get("/my/message-received")
async def function_my_message_received(request:Request,limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#message delete
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
@router.delete("/my/message-delete")
async def function_my_message_delete(request:Request,mode:str):
   #auth check
   response=await function_token_check(postgres_object,request,None)
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
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message inbox
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
@router.get("/my/message-inbox")
async def function_my_message_inbox(request:Request,mode:str=None,limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   if mode=="unread":query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message thread
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_token_check
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/my/message-thread")
async def function_my_message_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(postgres_object,request,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #update message status read
   query="update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   query_param={"status":"read","created_by_id":user_id,"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}
