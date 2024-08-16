#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#profile
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/{x}/my/profile")
async def function_my_profile(request:Request,background:BackgroundTasks):
   #prework
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
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #user extra info
   user_stats={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   temp={}
   for k,v in user_stats.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   return {"status":1,"message":temp}

#create object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization_values_list
@router.post("/{x}/my/create-object")
async def function_my_create_object(request:Request,table:str):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if table in ["users","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   body=await request.json()
   #query set
   column_to_insert_list=[item for item in [*body] if item not in ["id","created_at","is_active","is_verified","password","google_id","otp"]]+["created_by_id"]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   #values
   values={}
   for item in column_to_insert_list:values[item]=None
   #values assign
   for k,v in values.items():
      if k in body:values[k]=body[k]
   values["created_by_id"]=user["id"]
   #sanitization
   values_list=[values]
   response=await function_sanitization_values_list(request.state.postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#update object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
@router.post("/{x}/my/update-object")
async def function_my_update_object(request:Request,table:str,id:int):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #query set
   column_to_update_list=[item for item in [*body] if item not in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   #values
   values={}
   for item in column_to_update_list:values[item]=None
   values["id"]=None
   values["created_by_id"]=None
   #values assign
   for k,v in values.items():
      if k in body:values[k]=body[k]
   values["updated_at"]=datetime.now()
   values["updated_by_id"]=user["id"]
   values["id"]=user["id"] if table=="users" else id
   values["created_by_id"]=None if table=="users" else user["id"]
   #sanitization
   values_list=[values]
   response=await function_sanitization_values_list(request.state.postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#delete object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/my/delete-object")
async def function_my_delete_object(request:Request,table:str,id:int):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={}
   values["id"]=user["id"] if table=="users" else id
   values["created_by_id"]=None if table=="users" else user["id"]
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#read object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_prepare_where
@router.get("/{x}/my/read-object")
async def function_my_read_object(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   query_param=dict(request.query_params)
   query_param["created_by_id"]=f"{user['id']},="
   #where
   response=await function_prepare_where(request.state.postgres_object,query_param)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   where=response["message"][0]
   values=response["message"][1]
   #read object
   query=f"select * from {table} {where} order by {order} limit {limit} offset {(page-1)*limit};"
   values=values
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=[dict(item) for item in output]
   #final
   return {"status":1,"message":output}

#delete message
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/my/delete-message-all")
async def function_my_delete_message_all(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
   values={"created_by_id":user['id'],"parent_id":user['id']}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#message inbox
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/message-inbox")
async def function_my_message_inbox(request:Request,limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   values={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#message inbox unread
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/message-inbox-unread")
async def function_my_message_inbox_unread(request:Request,limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by id desc limit {limit} offset {(page-1)*limit};"
   values={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#message received
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/message-received")
async def function_my_message_received(request:Request,limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   values={"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#message thread
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from fastapi import BackgroundTasks
@router.get("/{x}/my/message-thread")
async def function_my_message_thread(request:Request,background:BackgroundTasks,user_id:int,limit:int=100,page:int=1):
   #prework
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

#message received
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/message-received")
async def function_my_message_received(request:Request,limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by id desc limit {limit} offset {(page-1)*limit};"
   values={"parent_id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#parent read
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/my/parent-read")
async def function_my_parent_read(request:Request,table:str,parent_table:str,limit:int=100,page:int=1):
   #prework
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
async def function_my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str,limit:int=100,page:int=1):
   #prework
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
