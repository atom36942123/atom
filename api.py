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
   for table in config_database["created_at"][1].split(','):
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #create column
   for k,v in config_database.items():
      for table in v[1].split(','):
         query=f"alter table {table} add column if not exists {k} {v[0]};"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set created_at default
   for table in config_database["created_at"][1].split(','):
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set protected rows
   for table in config_database["is_protected"][1].split(','):
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set not null
   for k,v in config_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #function call:schema_constraint_name_list
   response=await function_read_constraint_name_list(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_constraint_name_list=response["message"]
   #run query zzz
   for item in config_query_zzz:
      if item.split()[5] not in schema_constraint_name_list:
         query=item
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #function call:delete index all
   response=await function_delete_index_all(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   #function call:read schema column
   response=await function_read_schema_column(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_column=response["message"]
   #create index
   for column in schema_column:
      if column['column_name'] in config_column_to_index:
         query=f"create index if not exists index_{column['column_name']}_{column['table_name']} on {column['table_name']} using {config_datatype_index[column['data_type']]} ({column['column_name']});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
   
@router.post("/{x}/csv",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv(request:Request,file:UploadFile):
   #prework
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #function call:schema column datatype
   response=await function_read_schema_column_datatype(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_column_datatype=response["message"]
   #file
   filename=file.filename.split(".")[0]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_column_list=file_csv.fieldnames
   table=filename.rsplit("_",1)[0]
   mode=filename.rsplit("_",1)[1]
   #values list
   values_list=[]
   for row in file_csv:
      for column in file_column_list:
         if column not in schema_column_datatype:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"column not in the schema"}))
         if column in ["password","google_id"]:row[column]=hashlib.sha256(row[column].encode()).hexdigest() if row[column] else None  
         if schema_column_datatype[column] in ["jsonb"]:row[column]=json.dumps(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["ARRAY"]:row[column]=row[column].split(",") if row[column] else None
         if schema_column_datatype[column] in ["integer","bigint"]:row[column]=int(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["decimal","numeric","real","double precision"]:row[column]=round(float(row[column]),3) if row[column] else None
         if schema_column_datatype[column] in ["date","timestamp with time zone"]:row[column]=datetime.strptime(row[column],'%Y-%m-%d') if row[column] else None
      values_list.append(row)
   await file.close()
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
   for table in config_clean_table_creator:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #parent null
   for table in config_clean_table_parent:
      for parent_table in ["users","post","activity"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@router.get("/{x}/pcache")
@cache(expire=60)
async def function_pcache(request:Request):   
   #logic
   temp={}
   for k,v in config_pcache.items():
      query=v
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

@router.get("/{x}/feed")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_feed(request:Request):
   #prework
   body=dict(request.query_params)
   if body['table'] not in config_table_allowed_feed:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set (select * from :table :where :olo;)
   table=body["table"]
   order=body["order"] if "order" in body else "id desc"
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   where=""
   
   #where set
   param_where={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
   if param_where:
      where="where "
      for k,v in param_where.items():
         if f"{k}_operator" in body:where=where+f"({k}{body[f'{k}_operator']}:{k} or :{k} is null) and "
         else:where=where+f"({k}=:{k} or :{k} is null) and "
      where=where.strip().rsplit('and',1)[0]
   #function call:schema column datatype
   response=await function_read_schema_column_datatype(request.state.postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   schema_column_datatype=response["message"]
   #santized param_where
   for k,v in param_where.items():
      if schema_column_datatype[k] in ["ARRAY"]:param_where[k]=v.split(",")
      if schema_column_datatype[k] in ["integer","bigint"]:param_where[k]=int(v)
      if schema_column_datatype[k] in ["decimal","numeric","real","double precision"]:param_where[k]=float(v)
   #query run
   query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
   values=param_where
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=[dict(item) for item in output]   
   #function call:add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #function call:add action count
   response=await function_add_action_count(request.state.postgres_object,output,table,"activity","comment")
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
   temp={}
   for k,v in config_user_profile.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #background task
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":user|temp}

@router.post("/{x}/create")
async def function_create(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] not in config_table_allowed_create:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set (insert into :table :column_1 values :column_2;)
   table=body["table"]
   column_1=None
   column_2=None
   
   #body preprocessing
   body["created_by_id"]=user["id"]
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   
   
   
   
   #param set
   param={k:v for k,v in body.items() if (k not in ["table"]+["id","created_at","is_active","is_verified","google_id","otp"] and v not in [None,""," "])}
   column_1=','.join([*param])
   column_2=','.join([':'+item for item in [*param]])
   #query run
   query=f"insert into {table} ({column_1}) values ({column_2}) returning *;"
   values=param
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/update")
async def function_update(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #config
   config_table_allowed_update=["users","post","action","activity","box"]
   if body['table'] not in config_table_allowed_update:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body preprocessing
   body["updated_at"]=datetime.now()
   body["updated_by_id"]=user["id"]
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   #query set
   table=body["table"]
   column=""
   id=user["id"] if table=="users" else body["id"]
   created_by_id=None if table=="users" else user["id"]
   #param set
   param={k:v for k,v in body.items() if (k not in ["table","id"]+["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"] and v not in [None,""," "])}
   for k,v in param.items():column=column+f"{k}=coalesce(:{k},{k}),"
   column=column[:-1]
   #query run
   query=f"update {table} set {column} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   values=param|{"id":id,"created_by_id":created_by_id}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
   
@router.post("/{x}/delete")
async def function_delete(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #config
   config_table_allowed_delete=["users","post","action","activity"]
   if body['table'] not in config_table_allowed_delete:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set
   table=body["table"]
   id=user["id"] if table=="users" else body["id"]
   created_by_id=None if table=="users" else user["id"]
   #query run
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={"id":id,"created_by_id":created_by_id}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/read")
async def function_read(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #body preprocessing
   body["created_by_id"]=user["id"]
   #query set
   table=body["table"]
   where=""
   order=body["order"] if "order" in body else "id desc"
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #param set
   param={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
   if param:
      where="where "
      for k,v in param.items():
         if f"{k}_operator" in body:where=where+f"({k}{body[f'{k}_operator']}:{k} or :{k} is null) and "
         else:where=where+f"({k}=:{k} or :{k} is null) and "
      where=where.strip().rsplit('and',1)[0]
   #query run
   query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
   values=param
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
     
@router.post("/{x}/my")
async def function_my(request:Request,background:BackgroundTasks):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #pagination set
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #query set
   if body["mode"]=="message_inbox":
      query="with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit :limit offset :offset),y as (select a.* from x left join activity as a on x.id=a.id) select * from y order by id desc;"
      values={"created_by_id":user["id"],"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="message_inbox_unread":
      query="with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select a.* from x left join activity as a on x.id=a.id) select * from y where parent_id=:parent_id and status is null order by id desc limit :limit offset :offset;"
      values={"created_by_id":user["id"],"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="message_thread":
      query="select * from activity where type='message' and parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit :limit offset :offset;"
      values={"user_1":user["id"],"user_2":body["user_id"],"limit":limit,"offset":offset}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="message_received":
      query="select * from activity where type='message' and parent_table='users' and parent_id=:parent_id order by id desc limit :limit offset :offset;"
      values={"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="delete_message_all":
      query="delete from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
      values={"created_by_id":user['id'],"parent_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="read_parent_data":
      query=f"select parent_id from {body['table']} where created_by_id=:created_by_id and type=:type and parent_table=:parent_table order by id desc limit :limit offset :offset;"
      values={"created_by_id":user["id"],"type":body["type"],"parent_table":body["parent_table"],"limit":limit,"offset":offset}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      parent_ids=[item["parent_id"] for item in output]
      query=f"select * from {body['parent_table']} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if body["mode"]=="action_check":
      query=f"select parent_id from {body['table']} join unnest(array{body['ids']}::int[]) with ordinality t(parent_id, ord) using (parent_id) where created_by_id=:created_by_id and type=:type and parent_table=:parent_table;"
      values={"created_by_id":user["id"],"type":body["type"],"parent_table":body["parent_table"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      output=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #background task
   if body["mode"]=="message_thread":
      query="update activity set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where type='message' and parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      values={"status":"read","created_by_id":body["user_id"],"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/admin")
async def function_admin(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   body=dict(await request.json())
   #logic
   if body["mode"]=="update_cell":
      #schema column groupby
      query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
      #body preprocessing
      if body["column"] in ["password","google_id"]:body["value"]=hashlib.sha256(body["value"].encode()).hexdigest()
      if schema_column_datatype[body["column"]] in ["jsonb"]:body["value"]=json.dumps(body["value"])
      if schema_column_datatype[body["column"]] in ["ARRAY"]:body["value"]=body["value"].split(",")
      if schema_column_datatype[body["column"]] in ["integer","bigint"]:body["value"]=int(body["value"])
      if schema_column_datatype[body["column"]] in ["decimal","numeric","real","double precision"]:body["value"]=round(float(body["value"]),3)
      if schema_column_datatype[body["column"]] in ["date","timestamp with time zone"]:body["value"]=datetime.strptime(body["value"],'%Y-%m-%d')
      #logic
      query=f"update {body['table']} set {body['column']}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
      values={"value":body["value"],"id":body["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/aws")
async def function_aws(request:Request):
   #prework
   body=await request.json()
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #boto3
   s3_client=boto3.client("s3",region_name=config_s3_region,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   ses_client=boto3.client("ses",region_name=config_ses_region,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   #logic
   if body["mode"]=="s3_create":
      config_s3_link_expiry=1000
      config_s3_size_kb=300
      bucket_key=str(uuid.uuid4())+"-"+body["filename"]
      output=s3_client.generate_presigned_post(Bucket=config_s3_bucket,Key=bucket_key,ExpiresIn=config_s3_link_expiry,Conditions=[['content-length-range',1,config_s3_size_kb*1024]])
   if body["mode"]=="s3_delete":
      bucket_key=body["url"].split("/")[-1]
      output=s3_resource.Object(config_s3_bucket,bucket_key).delete()
   if body["mode"]=="s3_delete_all":
      output=s3_resource.Bucket(config_s3_bucket).objects.all().delete()
   if body["mode"]=="ses":
      output=ses_client.send_email(Source=config_ses_sender,Destination={"ToAddresses":[body["email"]]},Message={"Subject":{"Charset":"UTF-8","Data":body["title"]},"Body":{"Text":{"Charset":"UTF-8","Data":body["description"]}}})
   #final
   return {"status":1,"message":output}

@router.post("/{x}/mongo")
async def function_mongo(request:Request):
   #prework
   body=await request.json()
   config_mongo_url="mongodb://localhost:27017"
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_url)
   mode=body["mode"]
   body.pop("mode",None)
   #logic
   if mode=="create":
      response=await mongo_object.test.users.insert_one(body)
   if mode=="read":
      response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
   if mode=="update":
      id=body["id"]
      body.pop("id",None)
      response=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":body})
   if mode=="delete":
      response=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
   #final
   return response

@router.post("/{x}/elasticsearch")
async def function_elasticsearch(request:Request,mode:str):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=cloud_id,basic_auth=(username,password))
   mode=body["mode"]
   body.pop("mode",None)
   #table
   if "table" in body:
      table=body["table"]
      body.pop("table",None)
   #id
   if "id" in body:
      id=body["id"]
      body.pop("id",None)
   #logic
   if mode=="create":
      response=elasticsearch_object.index(index=table,id=id,document=body)
   if mode=="read":
      response=elasticsearch_object.get(index=table,id=id)
   if mode=="update":
      response=elasticsearch_object.update(index=table,id=id,doc=body)
   if mode=="delete":
      response=elasticsearch_object.delete(index=table,id=id)
   if mode=="refresh":
      response=elasticsearch_object.indices.refresh(index=table)
   if mode=="search":
      response=elasticsearch_object.search(index=table,body={"query":{"match":{column:body["keyword"]}},"size":body["size"]})
   #final
   return response

