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

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   return {"status":1,"message":output}

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   #prework
   config_database={"created_at":["timestamptz",1,"atom,users,post,likes,comment,bookmark,report,rating,block,message,helpdesk,file,otp,workseeker"],"created_by_id":["bigint",1,"atom,users,post,likes,comment,bookmark,report,rating,block,message,helpdesk,file,otp,workseeker"],"received_by_id":["bigint",1,"message"],"updated_at":["timestamptz",0,"atom,users,post,comment,report,message,helpdesk,workseeker"],"updated_by_id":["bigint",0,"atom,users,post,comment,report,message,helpdesk,workseeker"],"is_pinned":["int",1,"post"],"is_active":["int",1,"atom,users,post,comment,workseeker"],"is_verified":["int",1,"atom,users,post,comment,workseeker"],"parent_table":["text",1,"likes,comment,bookmark,report,rating,block"],"parent_id":["bigint",1,"likes,comment,bookmark,report,rating,block"],"firebase_id":["text",1,"users"],"google_id":["text",1,"users"],"last_active_at":["timestamptz",0,"users"],"otp":["int",1,"otp"],"username":["text",1,"users"],"password":["text",1,"users"],"profile_pic_url":["text",0,"users"],"date_of_birth":["date",0,"users"],"name":["text",0,"users,workseeker"],"gender":["text",0,"users,workseeker"],"email":["text",1,"users,post,otp,helpdesk,workseeker"],"mobile":["text",1,"users,post,otp,helpdesk,workseeker"],"whatsapp":["text",1,"users,post,workseeker"],"phone":["text",1,"users,post,workseeker"],"country":["text",1,"users,post"],"state":["text",1,"users,post"],"city":["text",1,"users,post"],"type":["text",1,"post,atom,users,helpdesk"],"title":["text",0,"post,atom,users"],"description":["text",0,"post,atom,users,comment,report,rating,block,message,helpdesk,workseeker"],"file_url":["text",0,"post,atom,file"],"link_url":["text",0,"post,atom"],"tag":["text[]",1,"post,atom,users,workseeker"],"date":["date",0,"post"],"status":["text",1,"post,report,message,helpdesk"],"remark":["text",0,"post,report,helpdesk"],"rating":["numeric",0,"post,rating,helpdesk"],"work_type":["text",1,"workseeker"],"work_profile":["text",1,"workseeker"],"degree":["text",0,"workseeker"],"college":["text",0,"workseeker"],"linkedin_url":["text",0,"workseeker"],"portfolio_url":["text",0,"workseeker"],"experience":["int",1,"workseeker"],"experience_work_profile":["int",0,"workseeker"],"is_working":["int",1,"workseeker"],"location_current":["text",1,"workseeker"],"location_expected":["text",1,"workseeker"],"currency":["text",0,"workseeker"],"salary_frequency":["text",0,"workseeker"],"salary_current":["int",0,"workseeker"],"salary_expected":["int",0,"workseeker"],"sector":["text",0,"workseeker"],"past_company_count":["int",0,"workseeker"],"past_company_name":["text",0,"workseeker"],"marital_status":["text",0,"workseeker"],"physical_disability":["text",0,"workseeker"],"hobby":["text",0,"workseeker"],"language":["text",0,"workseeker"],"joining_days":["int",1,"workseeker"],"career_break_month":["int",0,"workseeker"],"resume_url":["text",0,"workseeker"],"achievement":["text",0,"workseeker"],"certificate":["text",0,"workseeker"],"project":["text",0,"workseeker"],"is_founder":["int",1,"workseeker"],"soft_skill":["text",0,"workseeker"],"tool":["text",0,"workseeker"],"achievement_work":["text",0,"workseeker"],"metadata":["jsonb",0,"post"]}
   alter_query=["insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;","create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;",]
   mapping_datatype_index={"timestamptz":"brin","date":"brin","text[]":"gin","jsonb":"gin","int":"btree","numeric":"btree","bigint":"btree","text":"btree"}
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   for k,v in config_database.items():
      if len(v)!=3:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":f"{k} length issue"}))
   #logic
   [await request.state.postgres_object.fetch_all(query=f"create table if not exists {table} (id bigint primary key generated always as identity);",values={}) for table in config_database["created_at"][2].split(',')]
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} add column if not exists {k} {v[0]};",values={}) for k,v in config_database.items() for table in v[2].split(',')]
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column created_at set default now();",values={}) for table in config_database["created_at"][2].split(',')]
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} add constraint constraint_unique_{k.replace(',','_')+'_'+table} unique ({k});",values={}) for k,v in {"username":["users"],"created_by_id,parent_table,parent_id":["likes","bookmark","block","report"]}.items() for table in v if f"constraint_unique_{k.replace(',','_')+'_'+table}" not in constraint_name_list]
   [await request.state.postgres_object.fetch_all(query=query,values={}) for query in alter_query if query.split()[5] not in constraint_name_list]
   #index
   output=await request.state.postgres_object.fetch_all(query='''select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;''',values={})
   if output[0]["output"]:await request.state.postgres_object.fetch_all(query=output[0]["output"],values={})
   [await request.state.postgres_object.fetch_all(query=f"create index if not exists index_{k}_{table} on {table} using {mapping_datatype_index[v[0]]} ({k});",values={}) for k,v in config_database.items() for table in v[2].split(',') if v[1]==1]
   #response
   return {"status":1,"message":"done"}

@router.post("/{x}/insert-csv")
async def function_insert_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   mapping_column_datatype={item["column_name"]:item["datatype"] for item in await request.state.postgres_object.fetch_all(query="select column_name,max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name;",values={})}
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_column_name_list=list(set(file_object.fieldnames))
   #logic
   values=[]
   for row in file_object:
      for column in file_column_name_list:
         if mapping_column_datatype[column] in ["ARRAY"]:row[column]=row[column].split(",") if row[column] else None
         if mapping_column_datatype[column] in ["numeric"]:row[column]=round(float(row[column]),3) if row[column] else None
         if mapping_column_datatype[column] in ["jsonb"]:row[column]=json.dumps(row[column]) if row[column] else None
         if mapping_column_datatype[column] in ["integer","bigint"]:row[column]=int(row[column]) if row[column] else None
         if mapping_column_datatype[column] in ["date","timestamp with time zone"]:row[column]=datetime.strptime(row[column],'%Y-%m-%d') if row[column] else None
         if column in ["password","firebase_id","google_id"]:row[column]=hashlib.sha256(row[column].encode()).hexdigest() if row[column] else None  
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
   for item in ["username","email","mobile","otp"]:body[item]=body[item] if item in body else None
   for item in ["password","firebase_id","google_id"]:body[item]=hashlib.sha256(body[item].encode()).hexdigest() if item in body else None
   #otp verify
   if body["otp"]:
      output=await request.state.postgres_object.fetch_all(query="select * from otp where (email=:email or :email is null) and (mobile=:mobile or :mobile is null) order by id desc limit 1;",values={"email":body["email"],"mobile":body["mobile"]})
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
   #read user
   output=await request.state.postgres_object.fetch_all(query="select * from users where (username=:username or :username is null) and (password=:password or :password is null) and (email=:email or :email is null) and (mobile=:mobile or :mobile is null) and (firebase_id=:firebase_id or :firebase_id is null) and (google_id=:google_id or :google_id is null) order by id desc limit 1;",values={k:v for k,v in body.items() if k not in ["otp"]})
   user=output[0] if output else None
   #create user
   if not user and body["username"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   if not user:output=await request.state.postgres_object.fetch_all(query="insert into users (firebase_id,google_id,email,mobile) values (:firebase_id,:google_id,:email,:mobile) returning *;",values={k:v for k,v in body.items() if k not in ["otp","username","password"]})
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
   user=[dict(item) for item in output][0]
   #count key
   query_dict={"post_count":"select count(*) from post where created_by_id=:user_id;","comment_count":"select count(*) from comment where created_by_id=:user_id;","message_unread_count":"select count(*) from message where received_by_id=:user_id and status='unread';","like_post_count":"select count(*) from likes where created_by_id=:user_id and parent_table='post';","bookmark_post_count":"select count(*) from bookmark where created_by_id=:user_id and parent_table='post';",}
   for k,v in query_dict.items():
      output=await request.state.postgres_object.fetch_all(query=v,values={"user_id":user["id"]})
      user[k]=output[0]["count"]
   #response
   background_tasks.add_task(await request.state.postgres_object.fetch_all(query="update users set last_active_at=:last_active_at where id=:id;",values={"id":user["id"],"last_active_at":datetime.now()}))
   return {"status":1,"message":user}

@router.get("/{x}/my-message-inbox")
async def function_my_message_inbox(request:Request,page:int,is_unread:int=None,limit:int=30):
   #token check
   user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
   #logic
   query="with mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),x as (select owner_id,max(id) as id from mcr group by owner_id offset :offset limit :limit),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;"
   if is_unread==1:query='''with mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),x as (select owner_id,max(id) as id from mcr group by owner_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where received_by_id=:received_by_id and status='unread' order by id desc offset :offset limit :limit;'''
   output=await request.state.postgres_object.fetch_all(query=query,values={"created_by_id":user['id'],"received_by_id":user['id'],"offset":(page-1)*limit,"limit":limit})
   output=[dict(item) for item in output]
   #add user key
   if output:
      for user_column in ["created_by_id","received_by_id"]:
         output_user=await request.state.postgres_object.fetch_all(query=f"select * from users where id in ({','.join([str(item[user_column]) for item in output if item[user_column]])});",values={})
         for object in output:
            for user in output_user:
               if object[user_column]==user["id"]:
                  for key in ["username","profile_pic_url"]:
                     object[f"{user_column}_{key}"]=user[key]
                  break
            for key in ["username","profile_pic_url"]:object[f"{user_column}_{key}"]=None
   #response
   return {"status":1,"message":output}







# @router.get("/{x}/my-message-thread")
# async def function_my_message_thread(request:Request,user_id:int,page:int,background_tasks:BackgroundTasks,limit:int=30):
#    #token check
#    user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
#    if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
#       #logic

 

    
#     offset=(page-1)*limit
#     query=f"select * from message where (created_by_id=:user_1 and received_by_id=:user_2) or (created_by_id=:user_2 and received_by_id=:user_1) order by id desc offset {offset} limit {limit}"
#     values={"user_1":request_user["id"],"user_2":user_id}
#     response=await function_query_runner(request.state.postgres_object,"read",query,values)
#     if response["status"]==0:return function_http_response(400,0,response["message"])
#     #add user key
#     response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
#     if response["status"]==0:return function_http_response(400,0,response["message"])
#     response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"received_by_id")
#     if response["status"]==0:return function_http_response(400,0,response["message"])
#     #background task
#     query=f"update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where received_by_id=:received_by_id and created_by_id=:created_by_id returning *;"
#     values={"status":"read","updated_by_id":request_user['id'],"updated_at":datetime.now(),"received_by_id":request_user['id'],"created_by_id":user_id}
#     background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",query,values)
#     #final response
#     return response
   
   
    




   
   
