#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#profile
from fastapi import Request
from function import function_token_check_jwt
from fastapi import BackgroundTasks
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/profile")
async def function_my_profile(request:Request,background:BackgroundTasks):
   #postgres object
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #raise error
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #update last active at
   query="update users set last_active_at=:last_active_at where id=:id;"
   query_param={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":user}

#stats
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/stats")
async def function_my_stats(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #config
   user_stats={
   "post_count":"select count(*) as count from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) as count from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   #temp
   temp={}
   #logic
   for k,v in user_stats.items():
      query=v
      query_param={"user_id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output[0]["count"]
   #final
   return {"status":1,"message":temp}

#parent read
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #postgres object
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/parent-check")
async def function_my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #conversion
   parent_ids_list=[int(item) for item in parent_ids.split(",")]
   #read parent_ids from table
   query=f"select parent_id from {table} join unnest(array{parent_ids_list}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   parent_ids=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":parent_ids}
