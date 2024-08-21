#router
from fastapi import APIRouter
router=APIRouter(tags=["message"])

#import for raising error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import for auth check jwt
from config import config_key_jwt
import jwt
import json

#inbox
from fastapi import Request
@router.get("/{x}/message/inbox")
async def function_inbox(request:Request,limit:int=100,page:int=1):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#inbox unread
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/message/inbox-unread")
async def function_inbox_unread(request:Request,limit:int=100,page:int=1):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#thread
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/{x}/message/thread")
async def function_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #mark message status read
   query="update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   query_param={"status":"read","created_by_id":user_id,"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}

#received
from fastapi import Request
@router.get("/{x}/message/received")
async def function_received(request:Request,limit:int=100,page:int=1):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete message all
from fastapi import Request
@router.delete("/{x}/message/delete-all")
async def function_delete_all(request:Request):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
   query_param={"created_by_id":user['id'],"parent_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
