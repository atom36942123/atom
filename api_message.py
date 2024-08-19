#router
from fastapi import APIRouter
router=APIRouter(tags=["message"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check jwt
from config import config_key_jwt
import jwt
import json

#inbox
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/message/inbox")
async def function_inbox(request:Request,limit:int=100,page:int=1):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   values={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
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
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   values={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#thread
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from fastapi import BackgroundTasks
@router.get("/{x}/message/thread")
async def function_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit {limit} offset {(page-1)*limit};"
   values={"user_1":user["id"],"user_2":user_id}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #background
   query="update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   values={"status":"read","created_by_id":user_id,"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":output}

#received
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/message/received")
async def function_received(request:Request,limit:int=100,page:int=1):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   values={"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#delete message all
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/message/delete-all")
async def function_delete_all(request:Request):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
   values={"created_by_id":user['id'],"parent_id":user['id']}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
