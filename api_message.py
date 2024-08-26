#router
from fastapi import APIRouter
router=APIRouter(tags=["message"])

#inbox
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/message/inbox")
async def function_inbox(request:Request,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#inbox unread
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/message/inbox-unread")
async def function_inbox_unread(request:Request,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#thread
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_background_task_user
@router.get("/message/thread")
async def function_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background task
   response=await function_background_task_user(postgres_object,"mark_message_read",user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

#received
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/message/received")
async def function_received(request:Request,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete message all
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.delete("/message/delete-all")
async def function_delete_all(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
   query_param={"created_by_id":user['id'],"parent_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
