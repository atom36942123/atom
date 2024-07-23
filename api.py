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
from pydantic import BaseModel
from typing import Literal
from datetime import datetime,timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

config_database={"created_at":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"timestamptz",1],"created_by_id":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"bigint",1],"received_by_id":[["message"],"bigint",1],"updated_at":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"timestamptz",0],"updated_by_id":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"bigint",0],"is_pinned":[["post"],"int",1],"is_active":[["atom","users","post","comment","workseeker"],"int",1],"is_verified":[["atom","users","post","comment","workseeker"],"int",1],"parent_table":[["likes","comment","bookmark","report","rating","block"],"text",1],"parent_id":[["likes","comment","bookmark","report","rating","block"],"bigint",1],"firebase_id":[["users"],"text",1],"google_id":[["users"],"text",1],"last_active_at":[["users"],"timestamptz",0],"otp":[["otp"],"int",1],"username":[["users"],"text",1],"password":[["users"],"text",1],"profile_pic_url":[["users"],"text",0],"date_of_birth":[["users"],"date",0],"name":[["users","workseeker"],"text",0],"gender":[["users","workseeker"],"text",0],"email":[["users","post","otp","helpdesk","workseeker"],"text",1],"mobile":[["users","post","otp","helpdesk","workseeker"],"text",1],"whatsapp":[["users","post","workseeker"],"text",1],"phone":[["users","post","workseeker"],"text",1],"country":[["users","post"],"text",1],"state":[["users","post"],"text",1],"city":[["users","post"],"text",1],"type":[["post","atom","users","helpdesk"],"text",1],"title":[["post","atom","users"],"text",0],"description":[["post","atom","users","comment","report","rating","block","message","helpdesk","workseeker"],"text",0],"file_url":[["post","atom","file"],"text",0],"link_url":[["post","atom"],"text",0],"tag":[["post","atom","users","workseeker"],"text[]",1],"number":[["post"],"numeric",0],"date":[["post"],"date",0],"status":[["post","report","message","helpdesk"],"text",1],"remark":[["post","report","helpdesk"],"text",0],"rating":[["post","rating","helpdesk"],"int",0],"work_type":[["workseeker"],"text",1],"work_profile":[["workseeker"],"text",1],"degree":[["workseeker"],"text",0],"college":[["workseeker"],"text",0],"linkedin_url":[["workseeker"],"text",0],"portfolio_url":[["workseeker"],"text",0],"experience":[["workseeker"],"int",1],"experience_work_profile":[["workseeker"],"int",0],"is_working":[["workseeker"],"int",1],"location_current":[["workseeker"],"text",1],"location_expected":[["workseeker"],"text",1],"currency":[["workseeker"],"text",0],"salary_frequency":[["workseeker"],"text",0],"salary_current":[["workseeker"],"int",0],"salary_expected":[["workseeker"],"int",0],"sector":[["workseeker"],"text",0],"past_company_count":[["workseeker"],"int",0],"past_company_name":[["workseeker"],"text",0],"marital_status":[["workseeker"],"text",0],"physical_disability":[["workseeker"],"text",0],"hobby":[["workseeker"],"text",0],"language":[["workseeker"],"text",0],"joining_days":[["workseeker"],"int",1],"career_break_month":[["workseeker"],"int",0],"resume_url":[["workseeker"],"text",0],"achievement":[["workseeker"],"text",0],"certificate":[["workseeker"],"text",0],"project":[["workseeker"],"text",0],"is_founder":[["workseeker"],"int",1],"soft_skill":[["workseeker"],"text",0],"tool":[["workseeker"],"text",0],"achievement_work":[["workseeker"],"text",0],"alter_query":["alter table users add constraint constraint_unique_username_users unique (username);","alter table likes add constraint constraint_unique_created_by_id_parent_table_parent_id_likes unique (created_by_id,parent_table,parent_id);","alter table block add constraint constraint_unique_created_by_id_parent_table_parent_id_block unique (created_by_id,parent_table,parent_id);","insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;","create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;","create index if not exists index_parent_table_parent_id_likes on likes(parent_table,parent_id);","create index if not exists index_parent_table_parent_id_bookmark on bookmark(parent_table,parent_id);","create index if not exists index_parent_table_parent_id_comment on comment(parent_table,parent_id);"]}

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   return {"status":1,"message":output}

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   #prework
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   x={}
   for k,v in config_database.items():
      v[0]=",".join(v[0])
      x[k]=v
   return x
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   #logic
   for k,v in config_database.items():
      if k!="alter_query" and len(v)!=5:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":f"config_databae length issue {k}"}))
      if k=="created_at":[await request.state.postgres_object.fetch_all(query=f"create table if not exists {table} (id bigint primary key generated always as identity);",values={}) for table in v[0]]
      for table in v[0]:
         if k!="alter_query":await request.state.postgres_object.fetch_all(query=f"alter table {table} add column if not exists {k} {v[1]};",values={})
         if k!="alter_query" and v[2] is not None:await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column {k} set default {v[2]};",values={})
         if k!="alter_query" and v[3] is not None and f'checkin_{k}_{table}' not in schema_constraint_name_list:await request.state.postgres_object.fetch_all(query=f"alter table {table} add constraint {f'checkin_{k}_{table}'} check ({k} in {v[3]});",values={})
         if k!="alter_query" and v[4]==1 and "[]" in v[1]:await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table} using gin ({k});",values={})
         if k!="alter_query" and v[4]==1 and "[]" not in v[1]:await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table}({k});",values={})
      if k=="alter_query":[await request.state.postgres_object.fetch_all(query=item,values={}) for item in v if item.split()[5] not in schema_constraint_name_list]
   #response
   return {"status":1,"message":"done"}

@router.post("/{x}/insert-csv")
async def function_insert_csv(request:Request,table:str,file:UploadFile):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   values=[]
   for row in file_object:
      row["created_by_id"]=int(row["created_by_id"]) if row["created_by_id"] else None
      row["tag"]=row["tag"].split(",") if row["tag"] else None
      values.append(row)
   await request.state.postgres_object.execute_many(query=f"insert into {table} (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;",values=values)
   file.file.close
   #response    
   return {"status":1,"message":"done"}

@router.get("/{x}/metric")
async def function_metric(request:Request):
   output={"config_database_length":len(config_database)}
   return {"status":1,"message":output}



@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   body=await request.json()
   output=await request.state.postgres_object.fetch_all(query="insert into users (username,password) values (:username,:password) returning *;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})
   return {"status":1,"message":output}
 
@router.post("/{x}/login")
async def function_login(request:Request):
   #prework
   body,values=await request.json(),{}
   values["username"]=body["username"] if "username" in body else None
   values["password"]=hashlib.sha256(body["password"].encode()).hexdigest() if "password" in body else None
   values["email"]=body["email"] if "email" in body else None
   values["mobile"]=body["mobile"] if "mobile" in body else None
   values["firebase_id"]=hashlib.sha256(body["firebase_id"].encode()).hexdigest() if "firebase_id" in body else None
   values["google_id"]=hashlib.sha256(body["google_id"].encode()).hexdigest() if "google_id" in body else None
   #otp verify
   if "otp" in body:
      output=await request.state.postgres_object.fetch_all(query="select * from otp where (email=:email or :email is null) and (mobile=:mobile or :mobile is null) order by id desc limit 1;",values={"email":values["email"],"mobile":values["mobile"]})
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
   #read user
   output=await request.state.postgres_object.fetch_all(query="select * from users where (username=:username or :username is null) and (password=:password or :password is null) and (email=:email or :email is null) and (mobile=:mobile or :mobile is null) and (firebase_id=:firebase_id or :firebase_id is null) and (google_id=:google_id or :google_id is null) order by id desc limit 1;",values=values)
   user=output[0] if output else None
   #create user
   if not user and values["username"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   if not user:output=await request.state.postgres_object.fetch_all(query="insert into users (firebase_id,google_id,email,mobile) values (:firebase_id,:google_id,:email,:mobile) returning *;",values={"firebase_id":values["firebase_id"],"google_id":values["google_id"],"email":values["email"],"mobile":values["mobile"]})
   output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":output[0]["id"]})
   user=output[0]
   #token encode
   user={"x":str(request.url).split("/")[3],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   payload={"exp":time.mktime((datetime.now()+timedelta(days=int(1))).timetuple()),"data":json.dumps(user,default=str)}
   token=jwt.encode(payload,env("key"))
   #response
   return {"status":1,"message":token}

@router.get("/{x}/my-profile")
async def function_my_profile(request:Request,background_tasks:BackgroundTasks):
   #token check
   user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
   #read user
   output=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":user["id"]})
   user=output[0]
   #count key
   count={}
   query_dict={"post_count":"select count(*) from post where created_by_id=:user_id;","comment_count":"select count(*) from comment where created_by_id=:user_id;","message_unread_count":"select count(*) from message where received_by_id=:user_id and status='unread';","like_post_count":"select count(*) from likes where created_by_id=:user_id and parent_table='post';","bookmark_post_count":"select count(*) from bookmark where created_by_id=:user_id and parent_table='post';",}
   for k,v in query_dict.items():
      output=await request.state.postgres_object.fetch_all(query=v,values={"user_id":user["id"]})
      count[k]=output[0]["count"]
   #background task
   background_tasks.add_task(await request.state.postgres_object.fetch_all(query="update users set last_active_at=:last_active_at where id=:id;",values={"id":user["id"],"last_active_at":datetime.now()}))
   #response
   return {"status":1,"message":user|count}


   
   
