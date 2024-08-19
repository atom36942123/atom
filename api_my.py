#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check jwt
from config import config_key_jwt
import jwt
import json

#profile
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/{x}/my/profile")
async def function_my_profile(request:Request,background:BackgroundTasks):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #background
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":user}

#stats
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/stats")
async def function_my_stats(request:Request):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #config
   user_stats={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   #temp
   temp={}
   #logic
   for k,v in user_stats.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   return {"status":1,"message":temp}

#parent read
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select parent_id from {table} where parent_table=:parent_table and created_by_id=:created_by_id order by id desc limit {limit} offset {(page-1)*limit};"
   values={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   parent_ids=[item["parent_id"] for item in output]
   query=f"select * from {parent_table} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#parent check
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/parent-check")
async def function_my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   parent_ids_list=[int(item) for item in parent_ids.split(",")]
   query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
   values={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":output}
