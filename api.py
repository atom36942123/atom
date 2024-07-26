#router
from fastapi import APIRouter
router=APIRouter()

#env
from environs import Env
env=Env()
env.read_env()

#import
from fastapi import Request,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs,jwt,time
from datetime import datetime,timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#api
@router.get("/{x}/qrunner")
async def function_qrunner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   return output

@router.get("/{x}/database")
async def function_database(request:Request):
   #token
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #core
   config_database={"created_at":["timestamptz","users,post,action,activity,atom"],"created_by_id":["bigint","users,post,action,activity,atom"],"updated_at":["timestamptz","users,post,action,activity,atom"],"updated_by_id":["bigint","users,post,action,activity,atom"],"is_active":["int","users,post,action,activity,atom"],"is_verified":["int","users,post,action,activity,atom"],"is_protected":["int","users,post,atom"],"type":["text","users,post,action,activity,atom"],"parent_table":["text","action,activity"],"parent_id":["bigint","action,activity"],"status":["text","action,activity,atom"],"remark":["text","atom"],"metadata":["jsonb","post"],"username":["text","users"],"password":["text","users"],"google_id":["text","users"],"last_active_at":["timestamptz","users"],"name":["text","users"],"email":["text","users,atom"],"mobile":["text","users,atom"],"otp":["int","atom"],"title":["text","post,atom"],"description":["text","users,post,action,activity,atom"],"tag":["text","post"],"link":["text","post,atom"],"file":["text","post,atom"],"rating":["numeric","atom"]}
   [await request.state.postgres_object.fetch_all(query=f"create table if not exists {table} (id bigint primary key generated always as identity);",values={}) for table in config_database["created_at"][1].split(',')]
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} add column if not exists {k} {v[0]};",values={}) for k,v in config_database.items() for table in v[1].split(',')]
   #pattern
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column created_at set default now();",values={}) for table in config_database["created_at"][1].split(',')]
   [await request.state.postgres_object.fetch_all(query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;",values={}) for table in config_database["is_protected"][1].split(',')]
   #zzz
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   query_zzz=["alter table users add constraint constraint_unique_users unique (username);","alter table action add constraint constraint_unique_action unique (type,created_by_id,parent_table,parent_id);"]
   [await request.state.postgres_object.fetch_all(query=query,values={}) for query in query_zzz if query.split()[5] not in schema_constraint_name_list]
   #index
   output=await request.state.postgres_object.fetch_all(query='''select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;''',values={})
   if output[0]["output"]:await request.state.postgres_object.fetch_all(query=output[0]["output"],values={})
   schema_column=await request.state.postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public' order by column_name;",values={})
   mapping_index_datatype={"text":"btree","bigint":"btree","integer":"btree","numeric":"btree","timestamp with time zone":"brin","date":"brin","jsonb":"gin","ARRAY":"gin"}
   index_column=["type","is_verified","is_active","created_by_id","status","parent_table","parent_id","email","password","created_at"]
   [await request.state.postgres_object.fetch_all(query=f"create index if not exists index_{column['column_name']}_{column['table_name']} on {column['table_name']} using {mapping_index_datatype[column['data_type']]} ({column['column_name']});",values={}) for column in schema_column if column['column_name'] in index_column]
   #response
   return {"status":1,"message":"done"}

@router.post("/{x}/insert")
async def function_insert(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   schema_column_datatype={item["column_name"]:item["datatype"] for item in await request.state.postgres_object.fetch_all(query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;",values={})}
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_column_name_list=list(set(file_object.fieldnames))
   #logic
   values=[]
   for row in file_object:
      for column in file_column_name_list:
         if column not in schema_column_datatype:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"column not in database"}))
         if schema_column_datatype[column] in ["ARRAY"]:row[column]=row[column].split(",") if row[column] else None
         if schema_column_datatype[column] in ["numeric"]:row[column]=round(float(row[column]),3) if row[column] else None
         if schema_column_datatype[column] in ["jsonb"]:row[column]=json.dumps(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["integer","bigint"]:row[column]=int(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["date","timestamp with time zone"]:row[column]=datetime.strptime(row[column],'%Y-%m-%d') if row[column] else None
         if column in ["password","google_id"]:row[column]=hashlib.sha256(row[column].encode()).hexdigest() if row[column] else None  
      values.append(row)
   await request.state.postgres_object.execute_many(query=f"insert into {table} ({','.join(file_column_name_list)}) values ({','.join([':'+item for item in file_column_name_list])}) returning *;",values=values)
   file.file.close
   #response    
   return {"status":1,"message":"done"}

@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   body=await request.json()
   output=await request.state.postgres_object.fetch_all(query="insert into users (username,password) values (:username,:password) returning *;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})
   return {"status":1,"message":output}

@router.post("/{x}/login")
async def function_login(request:Request):
   #prework
   body=await request.json()
   #username
   if "username" in body:
      output=await request.state.postgres_object.fetch_all(query="select * from users where username=:username and password=:password order by id desc limit 1;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #google
   if "google_id" in body:
      output=await request.state.postgres_object.fetch_all(query="select * from users where google_id=:google_id order by id desc limit 1;",values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()})
      user=output[0] if output else None
      if not user:output=await request.state.postgres_object.fetch_all(query="insert into users (google_id) values (:google_id) returning *;",values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()})
      output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":output[0]["id"]})
      user=output[0]
   #email
   if "email" in body:
      output=await request.state.postgres_object.fetch_all(query="select otp from atom where type='otp' and email=:email order by id desc limit 1;",values={"email":body["email"]})
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
      output=await request.state.postgres_object.fetch_all(query="select * from users where email=:email order by id desc limit 1;",values={"email":body["email"]})
      user=output[0] if output else None
      if not user:output=await request.state.postgres_object.fetch_all(query="insert into users (email) values (:email) returning *;",values={"email":body["email"]})
      output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":output[0]["id"]})
      user=output[0]
   #mobile
   if "mobile" in body:
      output=await request.state.postgres_object.fetch_all(query="select otp from atom where type='otp' and mobile=:mobile order by id desc limit 1;",values={"mobile":body["mobile"]})
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
      output=await request.state.postgres_object.fetch_all(query="select * from users where mobile=:mobile order by id desc limit 1;",values={"mobile":body["mobile"]})
      user=output[0] if output else None
      if not user:output=await request.state.postgres_object.fetch_all(query="insert into users (mobile) values (:mobile) returning *;",values={"mobile":body["mobile"]})
      output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":output[0]["id"]})
      user=output[0]
   #token encode
   user={"x":str(request.url).split("/")[3],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   payload={"exp":time.mktime((datetime.now()+timedelta(days=int(1))).timetuple()),"data":json.dumps(user,default=str)}
   token=jwt.encode(payload,env("key"))
   #response
   return {"status":1,"message":token}

@router.get("/{x}/profile")
async def function_profile(request:Request,background:BackgroundTasks):
   #token check
   user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
   #read user
   output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":user["id"]})
   user=dict(output[0]) if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #count key
   query_dict={"post_count":"select count(*) from post where created_by_id=:user_id;","comment_count":"select count(*) from activity where type='comment' and created_by_id=:user_id;","message_unread_count":"select count(*) from activity where type='message' and parent_table='users' and parent_id=:user_id and status is null;"}
   for k,v in query_dict.items():
      output=await request.state.postgres_object.fetch_all(query=v,values={"user_id":user["id"]})
      user[k]=output[0]["count"]
   #response
   background.add_task(await request.state.postgres_object.fetch_all(query="update users set last_active_at=:last_active_at where id=:id;",values={"id":user["id"],"last_active_at":datetime.now()}))
   return {"status":1,"message":user}

@router.post("/{x}/object")
async def function_object(request:Request,background:BackgroundTasks):
   #token check
   user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
   #prework
   body=await request.json()
   mode=body["mode"]
   body.pop("mode",None)
   body={k:v for k,v in body.items() if v not in [None,""," "]}
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   #create
   if mode=="create":
      table=body["table"]
      if table=="users":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
      body["created_by_id"]=user["id"]
      for item in ["table","id","created_at","is_active","is_verified","google_id","otp"]:body.pop(item,None)
      column_1,column_2,=','.join([*body]),','.join([':'+item for item in [*body]])
      output=await request.state.postgres_object.fetch_all(query=f"insert into {table} ({column_1}) values ({column_2}) returning *;",values=body)
   #update
   if mode=="update":
      table,id=body["table"],body["id"]
      body["updated_at"],body["updated_by_id"]=datetime.now(),user["id"]
      for item in ["table","id","created_at","created_by_id","is_active","is_verified","type","google_id","otp"]:body.pop(item,None)
      key=""
      for k,v in body.items():key=key+f"{k}=coalesce(:{k},{k}) ,"
      column=key.strip().rsplit(',', 1)[0]
      if table=="users":output=await request.state.postgres_object.fetch_all(query=f"update {table} set {column} where id={user['id']} returning *;",values=body)
      else:output=await request.state.postgres_object.fetch_all(query=f"update {table} set {column} where id={id} and created_by_id={user['id']} returning *;",values=body)
   #delete
   if mode=="delete":
      table,id=body["table"],body["id"]
      if table=="users":output=await request.state.postgres_object.fetch_all(query=f"delete from {table} where id={user['id']};",values={})
      else:output=await request.state.postgres_object.fetch_all(query=f"delete from {table} where id={id} and created_by_id={user['id']};",values={})
   #response
   return {"status":1,"message":output}




    




   
   
