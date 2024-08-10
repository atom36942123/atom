#router
from fastapi import APIRouter
router = APIRouter()

#custom
from config import *
from function import *

#import
from fastapi import Request,Response,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs,jwt,time,boto3,uuid
from datetime import datetime,timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch

#api
@router.get("/{x}/qrunner")
async def function_qrunner(request:Request,query:str):
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   return output

@router.get("/{x}/database")
async def function_database(request:Request):
   #prework
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #create table
   config_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp"]
   for table in config_table:
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #create column
   config_column={
   "created_at":["timestamptz",config_table],
   "created_by_id":["bigint",config_table],
   "updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
   "updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
   "is_active":["int",["users","post"]],
   "is_verified":["int",["users","post"]],
   "is_protected":["int",["users","post","box","atom"]],
   "type":["text",["users","post","box","atom","helpdesk"]],
   "status":["text",["report","message","helpdesk"]],
   "remark":["text",["report","message","helpdesk"]],
   "metadata":["jsonb",["users","post","box","atom"]],
   "parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
   "parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
   "last_active_at":["timestamptz",["users"]],
   "google_id":["text",["users"]],
   "otp":["int",["otp"]],
   "username":["text",["users"]],
   "password":["text",["users"]],
   "name":["text",["users"]],
   "email":["text",["users","post","box","atom","otp"]],
   "mobile":["text",["users","post","box","atom","otp"]],
   "title":["text",["users","post","box","atom"]],
   "description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
   "tag":["text",["users","post","box","atom"]],
   "link":["text",["post","box","atom"]],
   "file":["text",["post","box","atom"]],
   "rating":["numeric",["rating"]],
   }
   for k,v in config_column.items():
      for table in v[1]:
         query=f"alter table {table} add column if not exists {k} {v[0]};"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set created_at default
   for table in config_table:
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set protected rows
   for table in config_column["is_protected"][1]:
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set not null
   config_column_not_null={"parent_table":["likes","bookmark","report","block","rating","comment","message"],"parent_id":["likes","bookmark","report","block","rating","comment","message"]}
   for k,v in config_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #run query zzz
   config_query_zzz=[
   "alter table users add constraint constraint_unique_users unique (username);",
   "alter table likes add constraint constraint_unique_likes unique (created_by_id,parent_table,parent_id);",
   "alter table bookmark add constraint constraint_unique_bookmark unique (created_by_id,parent_table,parent_id);",
   "alter table report add constraint constraint_unique_report unique (created_by_id,parent_table,parent_id);",
   "alter table block add constraint constraint_unique_block unique (created_by_id,parent_table,parent_id);",
   ]
   response=await function_read_constraint_name_list(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_constraint_name_list=response["message"]
   for item in config_query_zzz:
      if item.split()[5] not in schema_constraint_name_list:
         query=item
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #delete index all
   response=await function_delete_index_all(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   #create index
   config_datatype_index={"text":"btree","bigint":"btree","integer":"btree","numeric":"btree","timestamp with time zone":"brin","date":"brin","jsonb":"gin","ARRAY":"gin"}
   config_column_to_index=["type","is_verified","is_active","created_by_id","status","parent_table","parent_id","email","password","created_at"]
   response=await function_read_schema_column(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_column=response["message"]
   for column in schema_column:
      if column['column_name'] in config_column_to_index:
         query=f"create index if not exists index_{column['column_name']}_{column['table_name']} on {column['table_name']} using {config_datatype_index[column['data_type']]} ({column['column_name']});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

#body={"file":"atom_create.csv"}
@router.post("/{x}/csv",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv(request:Request,file:UploadFile):
   #prework
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #schema column datatype
   response=await function_read_column_datatype(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   mapping_column_datatype=response["message"]
   #file
   filename=file.filename.split(".")[0]
   table=filename.rsplit("_",1)[0]
   mode=filename.rsplit("_",1)[1]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_column_list=file_csv.fieldnames
   #values
   values_list=[]
   for row in file_csv:values_list.append(row)
   await file.close()
   #santization
   for index,object in enumerate(values_list):
      for k,v in object.items():
         datatype=mapping_column_datatype[k]
         if k in ["password","google_id"]:values_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if datatype in ["jsonb"]:values_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:values_list[index][k]=v.split(",") if v else None
         if datatype in ["integer","bigint"]:values_list[index][k]=int(v) if v else None
         if datatype in ["decimal","numeric","real","double precision"]:values_list[index][k]=round(float(v),3) if v else None
         if datatype in ["date","timestamp with time zone"]:values_list[index][k]=datetime.strptime(v,'%Y-%m-%d') if v else None
   #logic
   if mode=="create":
      column_to_insert_list=file_column_list
      query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
      values=values_list
      output=await request.state.postgres_object.execute_many(query=query,values=values)
   if mode=="read":
      ids_to_read=','.join([str(item["id"]) for item in values_list])
      query=f"select * from {table} where id in ({ids_to_read}) order by id desc;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if mode=="update":
      column_to_update_list=[item for item in file_column_list if item not in ["id"]]
      query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
      values=values_list
      output=await request.state.postgres_object.execute_many(query=query,values=values)
   if mode=="delete":
      query=f"delete from {table} where id=:id;"
      values=values_list
      output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   return {"status":1,"message":output}
   
@router.get("/{x}/clean")
async def function_clean(request:Request):
   #creator null
   config_clean_table_creator=["post","likes","bookmark","report","block","rating","comment","message"]
   for table in config_clean_table_creator:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #parent null
   config_clean_table_parent=["likes","bookmark","report","block","rating","comment","message"]
   for table in config_clean_table_parent:
      for parent_table in ["users","post","comment"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@router.get("/{x}/pcache")
@cache(expire=60)
async def function_pcache(request:Request):   
   #logic
   config_pcache={"user_count":"select count(*) from users;"}
   temp={}
   for k,v in config_pcache.items():
      query=v
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   return {"status":1,"message":temp}

@router.get("/{x}/feed")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_feed(request:Request):
   #prework
   body=dict(request.query_params)
   config_table_allowed_feed=["users","post","atom"]
   if body['table'] not in config_table_allowed_feed:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #read object
   response=await function_read_object(request.state.postgres_object,body,function_read_column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add action count
   response=await function_add_action_count(request.state.postgres_object,output,body["table"],"activity","comment")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}
   
@router.post("/{x}/signup")
async def function_signup(request:Request):
   body=await request.json()
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   return {"status":1,"message":output}

@router.post("/{x}/login")
async def function_login(request:Request):
   #prework
   body=await request.json()
   #username
   if "mode" not in body:
      query="select * from users where username=:username and password=:password order by id desc limit 1;"
      values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #google
   if "mode" in body and body["mode"]=="google":
      query="select * from users where google_id=:google_id order by id desc limit 1;"
      values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (google_id) values (:google_id) returning *;"
         values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user=output[0]
   #email
   if "mode" in body and body["mode"]=="email":
      response=await function_verify_otp(request.state.postgres_object,body["otp"],body["email"],None)
      if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body["email"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (email) values (:email) returning *;"
         values={"email":body["email"]}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user=output[0]
   #mobile
   if "mode" in body and body["mode"]=="mobile":
      response=await function_verify_otp(request.state.postgres_object,body["otp"],None,body["mobile"])
      if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body["mobile"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body["mobile"]}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user=output[0]
   #token encode
   config_token_expiry_days=1
   data_to_encode=json.dumps({"x":str(request.url.path).split("/")[1],"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=config_token_expiry_days)).timetuple()),"data":data_to_encode}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}
   
@router.get("/{x}/profile")
async def function_profile(request:Request,background:BackgroundTasks):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #add user object
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=dict(output[0]) if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #add extra info
   config_user_profile={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "comment_count":"select count(*) from activity where type='comment' and created_by_id=:user_id;",
   "message_unread_count":"select count(*) from activity where type='message' and parent_table='users' and parent_id=:user_id and status is null;"
   }
   temp={}
   for k,v in config_user_profile.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   background.add_task(await request.state.postgres_object.fetch_all(query="update users set last_active_at=:last_active_at where id=:id;",values={"last_active_at":datetime.now(),"id":user["id"]}))
   return {"status":1,"message":user|temp}

#body={"table":"post","type":"xxx","description":"xxx"}
#body={"table":"action","type":"like","parent_table":"post","parent_id":4}
#body={"table":"activity","type":"comment","parent_table":"post","parent_id":4,"description":"xxx"}
#body={"table":"activity","type":"message","parent_table":"users","parent_id":3,"description":"xxx"}
@router.post("/{x}/create")
async def function_create(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   config_table_allowed_create=["post","action","activity","box"]
   if body['table'] not in config_table_allowed_create:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set
   table=body["table"]
   column_to_insert_list=[item for item in [*body] if item not in ["table"]+["id","created_at","is_active","is_verified","google_id","otp"]]+["created_by_id"]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   #values
   values={}
   for item in column_to_insert_list:
      if item in body:values[item]=body[item]
      else:values[item]=None
   values["created_by_id"]=user["id"]
   if "metadata" in values:values["metadata"]=json.dumps(values["metadata"],default=str)
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#body={"table":"post","id":1,"title":"xxx","description":"xxx"}
#body={"table":"users","id":1,"name":"neo","gender":"male"}
@router.post("/{x}/update")
async def function_update(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #query set
   table=body["table"]
   column_to_update_list=[item for item in [*body] if item not in ["table","id"]+["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   #values
   values={}
   for item in column_to_update_list:
      if item in body:values[item]=body[item]
      else:values[item]=None
   values["updated_at"]=datetime.now()
   values["updated_by_id"]=user["id"]
   values["id"]=user["id"] if table=="users" else body["id"]
   values["created_by_id"]=None if table=="users" else user["id"]
   if "metadata" in values:values["metadata"]=json.dumps(values["metadata"],default=str)
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#body={"table":"post","order":"type desc","page":3,"limit":100,"id":9,"id_operator":">="}
@router.post("/{x}/read")
async def function_read(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #read object
   body["created_by_id"]=user["id"]
   response=await function_read_object(request.state.postgres_object,body,function_read_column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}

@router.post("/{x}/delete")
async def function_delete(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #logic
   #body={"mode":"object","table":"post","id":123}
   if body["mode"]=="object":
      table=body["table"]
      query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
      values={}
      values["id"]=user["id"] if table=="users" else body["id"]
      values["created_by_id"]=None if table=="users" else user["id"]
   #body={"mode":"message_all"}
   if body["mode"]=="message_all":
      query="delete from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
      values={"created_by_id":user['id'],"parent_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/my")
async def function_my(request:Request,background:BackgroundTasks):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #olo set
   order=body["order"] if "order" in body else "id desc"
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #logic
   #body={"mode":"message_inbox"}
   if body["mode"]=="message_inbox":
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {offset}),y as (select a.* from x left join activity as a on x.id=a.id) select * from y order by {order};"
      values={"created_by_id":user["id"],"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_inbox_unread"}
   if body["mode"]=="message_inbox_unread":
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select a.* from x left join activity as a on x.id=a.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {offset};"
      values={"created_by_id":user["id"],"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_received"}
   if body["mode"]=="message_received":
      query=f"select * from activity where type='message' and parent_table='users' and parent_id=:parent_id order by {order} limit {limit} offset {offset};"
      values={"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_thread","user_id":2}
   if body["mode"]=="message_thread":
      query=f"select * from activity where type='message' and parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {offset};"
      values={"user_1":user["id"],"user_2":body["user_id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      background.add_task(await request.state.postgres_object.fetch_all(query="update activity set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where type='message' and parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;",values={"status":"read","created_by_id":body["user_id"],"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}))
   #body={"mode":"read_parent_table_data","table":"action","parent_table":"post","type":"like"}
   if body["mode"]=="read_parent_table_data":pass
   #body={"mode":"check_action","table":"activity","parent_table":"post","ids":[1,2,3]"type":"comment"}
   if body["mode"]=="check_action":
      query=f"select parent_id from {body['table']} join unnest(array{body['ids']}::int[]) with ordinality t(parent_id, ord) using (parent_id) where created_by_id=:created_by_id and parent_table=:parent_table and type=:type;"
      values={"created_by_id":user["id"],"parent_table":body["parent_table"],"type":body["type"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      output=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":output}

@router.post("/{x}/admin")
async def function_admin(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   body=dict(await request.json())
   #logic
   #body={"mode":"update_cell","table":"users","id":12,"column":"name","value":"xxx"}
   if body["mode"]=="update_cell":
      if body["column"] in ["password","google_id"]:body["value"]=hashlib.sha256(body["value"].encode()).hexdigest()
      if body["column"] in ["metadata"]:body["value"]=json.dumps(body["value"])
      query=f"update {body['table']} set {body['column']}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
      values={"value":body["value"],"id":body["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/aws")
async def function_aws(request:Request):
   #prework
   body=await request.json()
   #logic
   #body={"mode":"s3_create_presigned_url","filename":"xxx.png"}
   if body["mode"]=="s3_create_presigned_url":
      output=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).generate_presigned_post(Bucket=config_s3_bucket_name,Key=str(uuid.uuid4())+"-"+body["filename"],ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
   #body={"mode":"s3_delete_bucket_key","url":"www.xxx.png/xxx"}
   if body["mode"]=="s3_delete_bucket_key":
      if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
      output=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).Object(config_s3_bucket_name,body["url"].rsplit("/",1)[1]).delete()
   #body={"mode":"s3_delete_bucket_key_all"}
   if body["mode"]=="s3_delete_bucket_key_all":
      if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
      output=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).Bucket(config_s3_bucket_name).objects.all().delete()
   #body={"mode":"ses_send_email","to":"atom36942@gmail.com","title":"xxx","description":"xxx"}
   if body["mode"]=="ses_send_email":
      output=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[body["to"]]},Message={"Subject":{"Charset":"UTF-8","Data":body["title"]},"Body":{"Text":{"Charset":"UTF-8","Data":body["description"]}}})
   #final
   return {"status":1,"message":output}

@router.post("/{x}/mongo")
async def function_mongo(request:Request):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   #body={"mode":"create","username":"xxx","age":33,"country":"korea"}
   if body["mode"]=="create":
      object={k:v for k,v in body.items() if k not in ["mode"]}
      output=await mongo_object.test.users.insert_one(object)
      response={"status":1,"message":repr(output.inserted_id)}
   #body={"mode":"read","id":"66b36a8a94d4da9c7652ef08"}
   if body["mode"]=="read":
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
      if output:output['_id']=str(output['_id'])
      response={"status":1,"message":output}
   #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob"}
   #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob","age":100}
   if body["mode"]=="update":
      key_to_update={k:v for k,v in body.items() if k not in ["mode","id"]}
      output=await mongo_object.test.users.update_one({"_id":ObjectId(body["id"])},{"$set":key_to_update})
      response={"status":1,"message":output.modified_count}
   #body={"mode":"delete","id":"66b36a8a94d4da9c7652ef08"}
   if body["mode"]=="delete":
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
      response={"status":1,"message":output.deleted_count}
   #final
   return response

@router.post("/{x}/elasticsearch")
async def function_elasticsearch(request:Request):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   #body={"mode":"create","table":"users","id":1,"username":"xxx","age":33,"country":"korea"}
   if body["mode"]=="create":
      object={k:v for k,v in body.items() if k not in ["mode","table","id"]}
      response=elasticsearch_object.index(index=body["table"],id=body["id"],document=object)
   #body={"mode":"read","table":"users","id":"1"}
   if body["mode"]=="read":
      response=elasticsearch_object.get(index=body["table"],id=body["id"])
   #{"mode":"update","table":"users","id":"1","username":"bob","age":100}
   if body["mode"]=="update":
      key_to_update={k:v for k,v in body.items() if k not in ["mode","table","id"]}
      response=elasticsearch_object.update(index=body["table"],id=body["id"],doc=key_to_update)
   #body={"mode":"delete","table":"users","id":"1"}
   if body["mode"]=="delete":
      response=elasticsearch_object.delete(index=body["table"],id=body["id"])
   #body={"mode":"refresh","table":"users"}
   if body["mode"]=="refresh":
      response=elasticsearch_object.indices.refresh(index=body["table"])
   #body={"mode":"search","table":"users","key":"username","keyword":"xxx","limit":1}
   if body["mode"]=="search":
      response=elasticsearch_object.search(index=body["table"],body={"query":{"match":{body["key"]:body["keyword"]}},"size":body["limit"]})
   #final
   return response

