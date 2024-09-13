#router
from fastapi import APIRouter
router=APIRouter(tags=["core"])

#postgres-init
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_init
@router.get("/postgres-init")
async def postgresinit(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#postgres clean
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_clean
@router.delete("/postgres-clean")
async def postgresclean(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
@router.post("/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def signup(request:Request,username:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
@router.post("/login")
async def login(request:Request,username:str,password:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login google
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgres_read_user_force
@router.post("/login-google")
async def login_google(request:Request,google_id:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_read_user_force(postgres_object,"google_id",google_id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login email
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.post("/login-email")
async def login_email(request:Request,email:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"email",email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login mobile
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.post("/login-mobile")
async def login_mobile(request:Request,mobile:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"mobile",mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#profile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from datetime import datetime
from function import postgres_object_update
@router.get("/profile")
async def profile(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response={"status":1,"message":user}
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   await postgres_object_update(postgres_object,column_datatype,"background","users",[object])
   #final
   return response

#token refresh
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import token_create
@router.get("/token-refresh")
async def token_refresh(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#delete account
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.get("/delete-account")
async def delete_account(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":"account deleted"}
   #final
   return response

#object create
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_create
@router.post("/object")
async def object_create(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","users","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["created_by_id"]=user["id"]
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/object")
async def object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#object update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_update
from function import postgres_object_ownership_check
@router.put("/object")
async def object_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["updated_by_id"]=user["id"]
   response=await postgres_object_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   if table=="users":
      for item in ["email","mobile"]:
         if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.delete("/object")
async def object_delete(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"delete from {table} {where_string};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#parent
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_parent_read
from function import postgres_parent_check
@router.get("/parent")
async def parent(request:Request,mode:str,table:str,parent_table:str,parent_ids:str=None,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="read":
      response=await postgres_parent_read(postgres_object,table,parent_table,order,limit,(page-1)*limit,user["id"])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   if mode=="check":
      if not parent_ids:return JSONResponse(status_code=400,content={"status":0,"message":"parent_ids is must"})
      response=await postgres_parent_check(postgres_object,table,parent_table,parent_ids,user["id"])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#message
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import BackgroundTasks
from datetime import datetime
from function import postgres_object_update
@router.get("/message")
async def message(request:Request,background:BackgroundTasks,mode:str,order:str="id desc",limit:int=100,page:int=1,user_id:int=None,message_id:int=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="received":
      query=f"select * from message where parent_table=:parent_table and parent_id=:parent_id order by {order} limit {limit} offset {(page-1)*limit};"
      query_param={"parent_table":"users","parent_id":user["id"]}
   if mode=="received_unread":
      query=f"select * from message where parent_table=:parent_table and parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
      query_param={"parent_table":"users","parent_id":user["id"]}
   if mode=="inbox":
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
      query_param={"parent_table":"users","created_by_id":user["id"],"parent_id":user["id"]}
   if mode=="inbox_unread":
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
      query_param={"parent_table":"users","created_by_id":user["id"],"parent_id":user["id"]}
   if mode=="thread":
      if not user_id:return JSONResponse(status_code=400,content={"status":0,"message":"user_id is must"})
      query=f"select * from message where parent_table=:parent_table and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
      query_param={"parent_table":"users","user_1":user["id"],"user_2":user_id}
   if mode=="delete_created_all":
      query="delete from message where parent_table=:parent_table and created_by_id=:created_by_id;"
      query_param={"parent_table":"users","created_by_id":user["id"]}
   if mode=="delete_received_all":
      query="delete from message where parent_table=:parent_table and parent_id=:parent_id;"
      query_param={"parent_table":"users","parent_id":user["id"]}
   if mode=="delete_all":
      query="delete from message where parent_table=:parent_table and (created_by_id=:created_by_id or parent_id=:parent_id);"
      query_param={"parent_table":"users","created_by_id":user["id"],"parent_id":user["id"]}
   if mode=="delete_single":
      if not message_id:return JSONResponse(status_code=400,content={"status":0,"message":"message_id is must"})
      query="delete from message where parent_table=:parent_table and id=:id and (created_by_id=:created_by_id or parent_id=:parent_id);"
      query_param={"parent_table":"users","id":message_id,"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background
   if mode=="thread":
      query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user["id"],"parent_id":user["id"]}
      background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   if mode in ["received","received_unread"]:
      object_list=[{"id":item["id"],"status":"read","updated_by_id":user["id"]} for item in output]
      response=await postgres_object_update(postgres_object,column_datatype,"background","message",object_list)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

#my
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgtes_otp_verify
from function import postgres_object_update
@router.get("/my")
async def my(request:Request,mode:str,table:str=None,ids:str=None,otp:int=None,email:str=None,mobile:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic      
   if mode=="delete_ids":
      if not table or not ids:return JSONResponse(status_code=400,content={"status":0,"message":"table/ids must"})
      if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
      if len(ids.split(","))>3:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
      query=f"delete from {table} where created_by_id=:created_by_id and id in ({ids});"
      query_param={"created_by_id":user["id"]}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      response={"status":1,"message":"ids deleted"}
   if mode=="update_email":
      if not otp or not email:return JSONResponse(status_code=400,content={"status":0,"message":"otp/email must"})
      response=await postgtes_otp_verify(postgres_object,otp,email,None)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      object={"id":user["id"],"updated_by_id":user["id"],"email":email}
      response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   if mode=="update_mobile":
      if not otp or not mobile:return JSONResponse(status_code=400,content={"status":0,"message":"otp/mobile must"})
      response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      object={"id":user["id"],"updated_by_id":user["id"],"mobile":mobile}
      response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#csv
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_create
from function import postgres_object_update
@router.post("/csv")
async def csv(request:Request,mode:str,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   if mode=="create":response=await postgres_object_create(postgres_object,column_datatype,"normal",table,object_list)
   if mode=="update":response=await postgres_object_update(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#qrunner
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.get("/qrunner")
async def qrunner(request:Request,mode:str,query:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="single":output=await postgres_object.fetch_all(query=query,values={})
   if mode=="bulk":output=[await postgres_object.fetch_all(query=item,values={}) for item in query.split("---")]
   #final
   return {"status":1,"message":output}

#location
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
from function import postgres_location_search
@router.get("/location")
async def location(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   response=await postgres_location_search(postgres_object,table,location,within,order,limit,(page-1)*limit,where_string,where_value)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#pcache
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from function import redis_key_builder
@router.get("/pcache")
@cache(expire=60,key_builder=redis_key_builder)
async def pcache(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   temp={k:await postgres_object.fetch_all(query=v,values={}) for k,v in query_dict.items()}
   response={"status":1,"message":temp}
   #final
   return response

#object read public
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
from function import postgres_add_creator_key
from function import postgres_add_action_count
from fastapi_cache.decorator import cache
from function import redis_key_builder
@router.get("/objectp")
@cache(expire=60,key_builder=redis_key_builder)
async def objectp_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response=await postgres_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   response=await postgres_add_action_count(postgres_object,"likes",table,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object read login
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/objectl")
async def objectl_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response

#object read admin
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/objecta")
async def objecta_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response

#object update admin
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_update
@router.put("/objecta")
async def objecta_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","otp","log"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["updated_by_id"]=user["id"]
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#otp
from fastapi import Request
from fastapi.responses import JSONResponse
import random,boto3
from config import aws_default_region,aws_access_key_id,aws_secret_access_key,ses_sender_email
from function import postgtes_otp_verify
@router.get("/otp")
async def otp(request:Request,mode:str,email:str=None,mobile:str=None,otp:int=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   if mode=="send_otp_mobile_sns":
      if not mobile:return JSONResponse(status_code=400,content={"status":0,"message":"mobile is must"})
      otp=random.randint(100000,999999)
      sns_client=boto3.client("sns",region_name=aws_default_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      output=sns_client.publish(PhoneNumber=mobile,Message=f"otp={otp}")
      query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;"
      query_param={"otp":otp,"mobile":mobile}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      response={"status":1,"message":"otp sent"}
   if mode=="send_otp_email_ses":
      if not email:return JSONResponse(status_code=400,content={"status":0,"message":"email is must"})
      otp=random.randint(100000,999999)
      ses_client=boto3.client("ses",region_name=aws_default_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      output=ses_client.send_email(Source=ses_sender_email,Destination={"ToAddresses":[email]},Message={"Subject":{"Charset":"UTF-8","Data":"otp"},"Body":{"Text":{"Charset":"UTF-8","Data":str(otp)}}})
      query="insert into otp (otp,email) values (:otp,:email) returning *;"
      query_param={"otp":otp,"email":email}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      response={"status":1,"message":"otp sent"}
   if mode=="otp_verify":
      if not otp:return JSONResponse(status_code=400,content={"status":0,"message":"otp is must"})
      if not email and not mobile:return JSONResponse(status_code=400,content={"status":0,"message":"email/mobile any ome is must"})
      response=await postgtes_otp_verify(postgres_object,otp,email,mobile)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#blob
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
import boto3,uuid
from config import aws_default_region,aws_access_key_id,aws_secret_access_key,s3_bucket_name
@router.get("/blob")
async def blob(request:Request,mode:str,filename:str=None,url:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="create_s3_url":
      if not filename:return JSONResponse(status_code=400,content={"status":0,"message":"filename must"})
      key=str(uuid.uuid4())+"-"+filename
      s3_client=boto3.client("s3",region_name=aws_default_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      output=s3_client.generate_presigned_post(Bucket=s3_bucket_name,Key=key,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
      response={"status":1,"message":output}
   if mode=="delete_s3_url":
      if user["type"] not in ["admin"]:return JSONResponse(status_code=400,content={"status":0,"message":"not allowed"})
      if not url:return JSONResponse(status_code=400,content={"status":0,"message":"url must"})
      key=url.rsplit("/",1)[1]
      s3_resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      output=s3_resource.Object(s3_bucket_name,key).delete()
      response={"status":1,"message":output}
   if mode=="delete_s3_all":
      if user["type"] not in ["admin"]:return JSONResponse(status_code=400,content={"status":0,"message":"not allowed"})
      s3_resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      output=s3_resource.Bucket(s3_bucket_name).objects.all().delete()
      response={"status":1,"message":output}
   #final
   return response
