#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#token refresh
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from function import function_token_create_jwt
from fastapi.responses import JSONResponse
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
   #raise error
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #token create
   response=await function_token_create_jwt(user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#profile
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi import BackgroundTasks
from datetime import datetime
from fastapi.responses import JSONResponse
@router.get("/my/profile")
async def function_my_profile(request:Request,background:BackgroundTasks):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #raise error
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #update last active at
   query="update users set last_active_at=:last_active_at where id=:id;"
   query_param={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":user}

#stats
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/my/stats")
async def function_my_stats(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   config_user_stats={
   "post_count":"select count(*) as x from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) as x from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   temp={}
   for k,v in config_user_stats.items():
      query=v
      query_param={"user_id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output[0]["x"]
   #final
   return {"status":1,"message":temp}

#parent read
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #read parent_ids from table
   query=f"select parent_id from {table} where parent_table=:parent_table and created_by_id=:created_by_id order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   parent_ids=[item["parent_id"] for item in output]
   #read parent_ids object
   query=f"select * from {parent_table} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#parent check
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/my/parent-check")
async def function_my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #conversion
   parent_ids_list=[int(item) for item in parent_ids.split(",")]
   #read parent_ids from table
   query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   parent_ids=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":parent_ids}

#read bulk
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/my/read-bulk")
async def function_my_read_bulk(request:Request,table:str,ids:str):
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
