#function
async def postgres_create(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list[0]:return {"status":0,"message":"object missing"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   column_insert_list=list(object_list[0].keys())
   query=f"insert into {table} ({','.join(column_insert_list)}) values ({','.join([':'+item for item in column_insert_list])}) on conflict do nothing returning *;"
   if len(object_list)==1:
      output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():
         output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_update(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list[0]:return {"status":0,"message":"object missing"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   column_update_list=[*object_list[0]]
   column_update_list.remove("id")
   query=f"update {table} set {','.join([f'{item}=:{item}' for item in column_update_list])} where id=:id returning *;"
   if len(object_list)==1:
      output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():
         output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_update_self(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize,user_id):
   if not object_list[0]:return {"status":0,"message":"object missing"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   column_update_list=[*object_list[0]]
   column_update_list.remove("id")
   query=f"update {table} set {','.join([f'{item}=:{item}' for item in column_update_list])} where id=:id and created_by_id={user_id} returning *;"
   if len(object_list)==1:
      output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():
         output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_delete(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list[0]:return {"status":0,"message":"object missing"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   query=f"delete from {table} where id=:id;"
   if len(object_list)==1:
      output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():
         output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string):
   order,limit,page=object.get("order","id desc"),int(object.get("limit",100)),int(object.get("page",1))
   column=object.get("column","*")
   location_filter=object.get("location_filter")
   if location_filter:
      location_filter_split=location_filter.split(",")
      long,lat,min_meter,max_meter=float(location_filter_split[0]),float(location_filter_split[1]),int(location_filter_split[2]),int(location_filter_split[3])
   response=await create_where_string(object,object_serialize,postgres_column_datatype)
   if response["status"]==0:return response
   where_string,where_value=response["message"][0],response["message"][1]
   if location_filter:query=f'''with x as (select * from {table} {where_string}),y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x) select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {(page-1)*limit};'''
   else:query=f"select {column} from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   object_list=await postgres_client.fetch_all(query=query,values=where_value)
   return {"status":1,"message":object_list}

import hashlib,datetime,json
async def object_serialize(postgres_column_datatype,object_list):
   for index,object in enumerate(object_list):
      for key,value in object.items():
         datatype=postgres_column_datatype.get(key)
         if not datatype:return {"status":0,"message":f"column {key} is not in postgres schema"}
         elif value==None:continue
         elif key in ["password"]:object_list[index][key]=hashlib.sha256(str(value).encode()).hexdigest()
         elif datatype=="text" and value in ["","null"]:object_list[index][key]=None
         elif datatype=="text":object_list[index][key]=value.strip()
         elif "int" in datatype:object_list[index][key]=int(value)
         elif datatype=="numeric":object_list[index][key]=round(float(value),3)
         elif datatype=="date":object_list[index][key]=datetime.datetime.strptime(value,'%Y-%m-%d')
         elif "time" in datatype:object_list[index][key]=datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%S')
         elif datatype=="ARRAY":object_list[index][key]=value.split(",")
         elif datatype=="jsonb":object_list[index][key]=json.dumps(value)
   return {"status":1,"message":object_list}

async def create_where_string(object,object_serialize,postgres_column_datatype):
   object={k:v for k,v in object.items() if (k in postgres_column_datatype and k not in ["metadata","location","table","order","limit","page"] and v is not None)}
   where_operator={k:v.split(',',1)[0] for k,v in object.items()}
   where_value={k:v.split(',',1)[1] for k,v in object.items()}
   response=await object_serialize(postgres_column_datatype,[where_value])
   if response["status"]==0:return response
   where_value=response["message"][0]
   where_string_list=[f"({key} {where_operator[key]} :{key} or :{key} is null)" for key in [*object]]
   where_string_joined=' and '.join(where_string_list)
   where_string=f"where {where_string_joined}" if where_string_joined else ""
   return {"status":1,"message":[where_string,where_value]}
   
async def verify_otp(postgres_client,otp,email,mobile):
   if not otp:return {"status":0,"message":"otp must"}
   if email:
      query="select otp from otp where created_at>current_timestamp-interval '10 minutes' and email=:email order by id desc limit 1;"
      output=await postgres_client.fetch_all(query=query,values={"email":email})
   if mobile:
      query="select otp from otp where created_at>current_timestamp-interval '10 minutes' and mobile=:mobile order by id desc limit 1;"
      output=await postgres_client.fetch_all(query=query,values={"mobile":mobile})
   if not output:return {"status":0,"message":"otp not found"}
   if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
   return {"status":1,"message":"done"}

async def postgres_schema_read(postgres_client):
   query='''
   WITH t AS (SELECT * FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'), 
   c AS (
   SELECT table_name, column_name, data_type, 
   CASE WHEN is_nullable='YES' THEN 1 ELSE 0 END AS is_nullable, 
   column_default 
   FROM information_schema.columns 
   WHERE table_schema='public'
   ), 
   i AS (
   SELECT t.relname::text AS table_name, a.attname AS column_name, 
   CASE WHEN idx.indisprimary OR idx.indisunique OR idx.indisvalid THEN 1 ELSE 0 END AS is_index
   FROM pg_attribute a
   JOIN pg_class t ON a.attrelid=t.oid
   JOIN pg_namespace ns ON t.relnamespace=ns.oid
   LEFT JOIN pg_index idx ON a.attrelid=idx.indrelid AND a.attnum=ANY(idx.indkey)
   WHERE ns.nspname='public' AND a.attnum > 0 AND t.relkind='r'
   )
   SELECT t.table_name as table, c.column_name as column, c.data_type as datatype,c.column_default as default, c.is_nullable as is_null, COALESCE(i.is_index, 0) AS is_index 
   FROM t 
   LEFT JOIN c ON t.table_name=c.table_name 
   LEFT JOIN i ON t.table_name=i.table_name AND c.column_name=i.column_name;
   '''
   output=await postgres_client.fetch_all(query=query,values={})
   postgres_schema={}
   for object in output:
      table,column=object["table"],object["column"]
      column_data={"datatype":object["datatype"],"default":object["default"],"is_null":object["is_null"],"is_index":object["is_index"]}
      if table not in postgres_schema:postgres_schema[table]={}
      postgres_schema[table][column]=column_data
   return postgres_schema

async def postgres_schema_init(postgres_client,postgres_schema_read,config):
   #extension
   await postgres_client.fetch_all(query="create extension if not exists postgis;",values={})
   await postgres_client.fetch_all(query="create extension if not exists pg_trgm;",values={})
   #table
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      is_table=postgres_schema.get(table,{})
      if not is_table:
         query=f"create table if not exists {table} (id bigint primary key generated always as identity not null);"
         await postgres_client.execute(query=query,values={})
   #column
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         is_column=postgres_schema.get(table,{}).get(column_name,{})
         if not is_column:
            query=f"alter table {table} add column if not exists {column_name} {column_datatype};"
            await postgres_client.execute(query=query,values={})
   #nullable
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         is_null=postgres_schema.get(table,{}).get(column_name,{}).get("is_null",None)
         if column_is_mandatory=="0" and is_null==0:
            query=f"alter table {table} alter column {column_name} drop not null;"
            await postgres_client.execute(query=query,values={})
         if column_is_mandatory=="1" and is_null==1:
            query=f"alter table {table} alter column {column_name} set not null;"
            await postgres_client.execute(query=query,values={})
   #index
   postgres_schema=await postgres_schema_read(postgres_client)
   index_name_list=[object["indexname"] for object in (await postgres_client.fetch_all(query="SELECT indexname FROM pg_indexes WHERE schemaname='public';",values={}))]
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         if column_index_type=="0":
            query=f"DO $$ DECLARE r RECORD; BEGIN FOR r IN (SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname ILIKE 'index_{table}_{column_name}_%') LOOP EXECUTE 'DROP INDEX IF EXISTS public.' || quote_ident(r.indexname); END LOOP; END $$;"
            await postgres_client.execute(query=query,values={})
         else:
            index_type_list=column_index_type.split(",")
            for index_type in index_type_list:
               index_name=f"index_{table}_{column_name}_{index_type}"
               if index_name not in index_name_list:
                  if index_type=="gin":
                     query=f"create index concurrently if not exists {index_name} on {table} using {index_type} ({column_name} gin_trgm_ops);"
                     await postgres_client.execute(query=query,values={})
                  else:
                     query=f"create index concurrently if not exists {index_name} on {table} using {index_type} ({column_name});"
                     await postgres_client.execute(query=query,values={})
   #query
   constraint_name_list={object["constraint_name"].lower() for object in (await postgres_client.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={}))}
   for query in config["query"].values():
      if query.split()[0]=="0":continue
      if "add constraint" in query.lower() and query.split()[5].lower() in constraint_name_list:continue
      await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":"done"}

from google.oauth2 import id_token
from google.auth.transport import requests
def verify_google_token(google_client_id,google_token):
   try:
      request=requests.Request()
      id_info=id_token.verify_oauth2_token(google_token,request,google_client_id)
      output={"sub": id_info.get("sub"),"email": id_info.get("email"),"name": id_info.get("name"),"picture": id_info.get("picture"),"email_verified": id_info.get("email_verified")}
      response={"status":1,"message":output}
   except Exception as e:response={"status":0,"message":str(e)}
   return response

async def ownership_check(postgres_client,table,id,user_id):
   if table=="users":
      if id!=user_id:return {"status":0,"message":"object ownership issue"}
   if table!="users":
      output=await postgres_client.fetch_all(query=f"select created_by_id from {table} where id=:id;",values={"id":id})
      if not output:return {"status":0,"message":"no object"}
      if output[0]["created_by_id"]!=user_id:return {"status":0,"message":"object ownership issue"}
   return {"status":1,"message":"done"}

async def add_creator_data(postgres_client,object_list,user_key):
   if not object_list:return {"status":1,"message":object_list}
   object_list=[dict(object) for object in object_list]
   created_by_ids={str(object["created_by_id"]) for object in object_list if object.get("created_by_id")}
   if created_by_ids:
      query=f"select * from users where id in ({','.join(created_by_ids)});"
      users={user["id"]:dict(user) for user in await postgres_client.fetch_all(query=query, values={})}
   for object in object_list:
      if object["created_by_id"] in users:
         for key in user_key.split(","):object[f"creator_{key}"]=users[object["created_by_id"]][key]
      else:
         for key in user_key.split(","):object[f"creator_{key}"]=None    
   return {"status":1,"message":object_list}

import uuid
from io import BytesIO
async def s3_file_upload(s3_client,s3_region_name,bucket,key_list,file_list):
   if not key_list:key_list=[f"{uuid.uuid4().hex}.{file.filename.rsplit('.',1)[1]}" for file in file_list]
   output={}
   for index,file in enumerate(file_list):
      key=key_list[index]
      if "." not in key:return {"status":0,"message":"extension must"}
      file_content=await file.read()
      file_size_kb=round(len(file_content)/1024)
      if file_size_kb>100:return {"status":0,"message":f"{file.filename} has {file_size_kb} kb size which is not allowed"}
      s3_client.upload_fileobj(BytesIO(file_content),bucket,key)
      output[file.filename]=f"https://{bucket}.s3.{s3_region_name}.amazonaws.com/{key}"
      file.file.close()
   return {"status":1,"message":output}
     
import csv,io
async def file_to_object_list(file):
   content=await file.read()
   content=content.decode("utf-8")
   reader=csv.DictReader(io.StringIO(content))
   object_list=[row for row in reader]
   await file.close()
   return object_list

async def form_data_read(request):
   form_data=await request.form()
   form_data_key={key:value for key,value in form_data.items() if isinstance(value,str)}
   form_data_file=[file for key,value in form_data.items() for file in form_data.getlist(key)  if key not in form_data_key and file.filename]
   return form_data_key,form_data_file

import json
async def redis_set_object(redis_client,key,expiry,object):
   object=json.dumps(object)
   if not expiry:output=await redis_client.set(key,object)
   else:output=await redis_client.setex(key,expiry,object)
   return {"status":1,"message":output}

import json
async def redis_get_object(redis_client,key):
   output=await redis_client.get(key)
   if output:output=json.loads(output)
   return {"status":1,"message":output}

import jwt,json
async def token_create(key_jwt,user):
   token_expire_sec=365*24*60*60
   user={"id":user["id"],"type":user["type"]}
   user=json.dumps(user,default=str)
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":user},key_jwt)
   return token

async def request_user_read(request):
   query="select * from users where id=:id;"
   values={"id":request.state.user["id"]}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=dict(output[0]) if output else None
   response={"status":1,"message":user}
   if not user:response={"status":0,"message":"user not found"}
   return response

async def admin_check(request,api,api_id,users_api_access,postgres_client):
   if "admin/" not in api:return {"status":1,"message":"done"}
   api_id_value=api_id.get(api)
   if not api_id_value:return {"status":0,"message":"api id not mapped in backend"}
   user_api_access=users_api_access.get(request.state.user["id"],"absent")
   if user_api_access=="absent":
      output=await postgres_client.fetch_all(query="select id,api_access from users where id=:id;",values={"id":request.state.user["id"]})
      user=output[0] if output else None
      if not user:return {"status":0,"message":"user not found"}
      api_access_str=user["api_access"]
      if not api_access_str:return {"status":0,"message":"api access denied"}
      user_api_access=[int(item.strip()) for item in api_access_str.split(",")]
   if api_id_value not in user_api_access:return {"status":0,"message":"api access denied"}
   return {"status":1,"message":"done"}

async def is_active_check(request,api,users_is_active):
   for item in ["admin/","private","my/object-create"]:
      if item in api:
         user_is_active=users_is_active.get(request.state.user["id"],"absent")
         if user_is_active=="absent":
            output=await postgres_client.fetch_all(query="select id,is_active from users where id=:id;",values={"id":request.state.user["id"]})
            user=output[0] if output else None
            if not user:return {"status":0,"message":"user not found"}
            user_is_active=user["is_active"]
         if user_is_active==0:return {"status":0,"message":"user not active"}
   return {"status":1,"message":"done"}

from fastapi import responses
def error(message):
   return responses.JSONResponse(status_code=400,content={"status":0,"message":message})

#env
import os,json
from dotenv import load_dotenv
load_dotenv()
postgres_url=os.getenv("postgres_url")
redis_url=os.getenv("redis_url")
key_jwt=os.getenv("key_jwt")
key_root=os.getenv("key_root")
valkey_url=os.getenv("valkey_url")
sentry_dsn=os.getenv("sentry_dsn")
mongodb_url=os.getenv("mongodb_url")
rabbitmq_url=os.getenv("rabbitmq_url")
lavinmq_url=os.getenv("lavinmq_url")
kafka_url=os.getenv("kafka_url")
kafka_path_cafile=os.getenv("kafka_path_cafile")
kafka_path_certfile=os.getenv("kafka_path_certfile")
kafka_path_keyfile=os.getenv("kafka_path_keyfile")
aws_access_key_id=os.getenv("aws_access_key_id")
aws_secret_access_key=os.getenv("aws_secret_access_key")
s3_region_name=os.getenv("s3_region_name")
sns_region_name=os.getenv("sns_region_name")
ses_region_name=os.getenv("ses_region_name")
ses_sender_email=os.getenv("ses_sender_email")
google_client_id=os.getenv("google_client_id")
is_signup=int(os.getenv("is_signup",0))
postgres_url_read=os.getenv("postgres_url_read")

#config
user_type_allowed=[1,2,3]
channel_name="ch1"
column_disabled_non_admin=["is_active","is_verified","api_access"]
api_id={
"/admin/db-runner":1,
"/admin/user-create":2,
"/admin/object-create":3,
"/admin/user-update":4,
"/admin/object-update":5,
"/admin/ids-update":6,
"/admin/ids-delete":7,
"/admin/object-read":8
}
postgres_config={
"table":{
"test":[
"created_at-timestamptz-0-brin",
"updated_at-timestamptz-0-0",
"created_by_id-bigint-0-0",
"updated_by_id-bigint-0-0",
"is_active-smallint-0-btree",
"is_verified-smallint-0-btree",
"is_deleted-smallint-0-btree",
"is_protected-smallint-0-btree",
"type-smallint-0-btree",
"title-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"link_url-text-0-0",
"tag-text-0-0",
"rating-numeric(10,3)-0-0",
"remark-text-0-gin,btree",
"location-geography(POINT)-0-gist",
"metadata-jsonb-0-0"
],
"log_api":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-0",
"api-text-0-0",
"method-text-0-0",
"query_param-text-0-0",
"status_code-smallint-0-0",
"response_time_ms-numeric(1000,3)-0-0",
"description-text-0-0"
],
"otp":[
"created_at-timestamptz-0-brin",
"otp-integer-1-0",
"email-text-0-btree",
"mobile-text-0-btree"
],
"log_password":[
"created_at-timestamptz-0-0",
"user_id-bigint-0-0",
"password-text-0-0"
],
"users":[
"created_at-timestamptz-0-brin",
"updated_at-timestamptz-0-0",
"created_by_id-bigint-0-0",
"updated_by_id-bigint-0-0",
"is_active-smallint-0-btree",
"is_verified-smallint-0-btree",
"is_deleted-smallint-0-btree",
"is_protected-smallint-0-btree",
"type-smallint-1-btree",
"username-text-0-btree",
"password-text-0-btree",
"google_id-text-0-btree",
"google_data-jsonb-0-0",
"email-text-0-btree",
"mobile-text-0-btree",
"api_access-text-0-0",
"last_active_at-timestamptz-0-0"
],
"message":[
"created_at-timestamptz-0-brin",
"updated_at-timestamptz-0-0",
"created_by_id-bigint-1-btree",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"user_id-bigint-1-btree",
"description-text-1-0",
"is_read-smallint-0-btree"
],
"report_user":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-1-btree",
"user_id-bigint-1-btree"
],
"bookmark_workseeker":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-1-btree",
"workseeker_id-bigint-1-btree"
],
"work_profile":[
"title-text-1-0"
],
"workseeker":[
"created_at-timestamptz-0-brin",
"updated_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_by_id-bigint-0-0",
"is_active-smallint-0-btree",
"is_deleted-smallint-0-btree",
"type-smallint-0-btree",
"work_profile_id-int-0-btree",
"experience-numeric(10,1)-0-btree",
"skill-text-0-0",
"description-text-0-0",
"salary_currency-text-0-0",
"salary_current-int-0-0",
"salary_expected-int-0-0",
"notice_period-smallint-0-0",
"college-text-0-0",
"degree-text-0-0",
"industry-text-0-0",
"certification-text-0-0",
"achievement-text-0-0",
"hobby-text-0-0",
"life_goal-text-0-0",
"strong_point-text-0-0",
"weak_point-text-0-0",
"name-text-0-0",
"gender-text-0-0",
"date_of_birth-date-0-0",
"nationality-text-0-0",
"language-text-0-0",
"email-text-0-0",
"mobile-text-0-0",
"country-text-0-0",
"state-text-0-0",
"city-text-0-0",
"current_location-text-0-0",
"is_remote-smallint-0-0",
"linkedin_url-text-0-0",
"github_url-text-0-0",
"portfolio_url-text-0-0",
"website_url-text-0-0",
"resume_url-text-0-0"
]
},
"query":{
"drop_all_index":"0 DO $$ DECLARE r RECORD; BEGIN FOR r IN (SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'index_%') LOOP EXECUTE 'DROP INDEX IF EXISTS public.' || quote_ident(r.indexname); END LOOP; END $$;",
"default_created_at":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name='created_at' AND table_schema='public') LOOP EXECUTE FORMAT('ALTER TABLE ONLY %I ALTER COLUMN created_at SET DEFAULT NOW();', tbl.table_name); END LOOP; END $$;",
"default_updated_at_1":"create or replace function function_set_updated_at_now() returns trigger as $$ begin new.updated_at=now(); return new; end; $$ language 'plpgsql';",
"default_updated_at_2":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name='updated_at' AND table_schema='public') LOOP EXECUTE FORMAT('CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_%I BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION function_set_updated_at_now();', tbl.table_name, tbl.table_name); END LOOP; END $$;",
"is_protected":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name='is_protected' AND table_schema='public') LOOP EXECUTE FORMAT('CREATE OR REPLACE RULE rule_protect_%I AS ON DELETE TO %I WHERE OLD.is_protected=1 DO INSTEAD NOTHING;', tbl.table_name, tbl.table_name); END LOOP; END $$;",
"delete_disable_bulk_1":"create or replace function function_delete_disable_bulk() returns trigger language plpgsql as $$declare n bigint := tg_argv[0]; begin if (select count(*) from deleted_rows) <= n is not true then raise exception 'cant delete more than % rows', n; end if; return old; end;$$;",
"delete_disable_bulk_2":"create or replace trigger trigger_delete_disable_bulk_users after delete on users referencing old table as deleted_rows for each statement execute procedure function_delete_disable_bulk(1);",
"log_password_1":"CREATE OR REPLACE FUNCTION function_log_password_change() RETURNS TRIGGER LANGUAGE PLPGSQL AS $$ BEGIN IF OLD.password <> NEW.password THEN INSERT INTO log_password(user_id,password) VALUES(OLD.id,OLD.password); END IF; RETURN NEW; END; $$;",
"log_password_2":"CREATE OR REPLACE TRIGGER trigger_log_password_change AFTER UPDATE ON users FOR EACH ROW WHEN (OLD.password IS DISTINCT FROM NEW.password) EXECUTE FUNCTION function_log_password_change();",
"root_user_1":"insert into users (type,username,password,api_access) values (1,'atom','5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5','1,2,3,4,5,6,7,8,9,10') on conflict do nothing;",
"root_user_2":"create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;",
"default_1":"0 alter table users alter column is_active set default 1;",
"unique_1":"alter table users add constraint constraint_unique_users_type_username unique (type,username);",
"unique_2":"alter table users add constraint constraint_unique_users_type_google_id unique (type,google_id);",
"unique_3":"alter table users add constraint constraint_unique_users_type_email unique (type,email);",
"unique_4":"alter table users add constraint constraint_unique_users_type_mobile unique (type,mobile);",
"unique_5":"alter table workseeker add constraint constraint_unique_created_by_id unique (created_by_id);",
"unique_6":"alter table report_user add constraint constraint_unique_report_user unique (created_by_id,user_id);",
"unique_7":"alter table bookmark_workseeker add constraint constraint_unique_bookmark_workseeker unique (created_by_id,workseeker_id);",
"check_1":"alter table users add constraint constraint_check_users_username check (username = lower(username) and username not like '% %' and trim(username) = username);",
"check_2":"DO $$ DECLARE r RECORD; constraint_name TEXT; BEGIN FOR r IN (SELECT c.table_name FROM information_schema.columns c JOIN pg_class p ON c.table_name = p.relname JOIN pg_namespace n ON p.relnamespace = n.oid WHERE c.column_name = 'is_active' AND c.table_schema = 'public' AND p.relkind = 'r') LOOP constraint_name := format('constraint_check_%I_is_active', r.table_name); IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = constraint_name) THEN EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK (is_active IN (0,1) OR is_active IS NULL);', r.table_name, constraint_name); END IF; END LOOP; END $$;"
}
}

#setters
postgres_client=None
postgres_client_read=None
postgres_client_asyncpg=None
from databases import Database
import asyncpg
async def set_postgres_client():
   global postgres_client
   global postgres_client_asyncpg
   global postgres_client_read
   postgres_client=Database(postgres_url,min_size=1,max_size=100)
   postgres_client_asyncpg=await asyncpg.connect(postgres_url)
   if postgres_url_read:postgres_client_read=Database(postgres_url_read,min_size=1,max_size=100)
   await postgres_client.connect()
   return None

postgres_schema={}
postgres_column_datatype={}
async def set_postgres_schema():
   global postgres_schema
   global postgres_column_datatype
   postgres_schema=await postgres_schema_read(postgres_client)
   postgres_column_datatype={k:v["datatype"] for table,column in postgres_schema.items() for k,v in column.items()}
   return None

users_api_access={}
async def set_users_api_access():
   global users_api_access
   local_users_api_access={}
   if postgres_schema.get("users"):
      try:
         async with postgres_client_asyncpg.transaction():
            cursor=await postgres_client_asyncpg.cursor('SELECT id,api_access FROM users where api_access is not null ORDER BY id DESC')
            count=0
            while count < 100000:
               batch=await cursor.fetch(10000)
               if not batch:break
               local_users_api_access.update({record['id']:[int(item.strip()) for item in record["api_access"].split(",")] for record in batch})
               if False:await redis_client.mset({f"users_api_access_{record['id']}":record['api_access'] for record in batch})
               count+=len(batch)
      except Exception as e:print(f"Error in set_users_api_access: {e}")
      users_api_access=local_users_api_access
   return None

users_is_active={}
async def set_users_is_active():
   global users_is_active
   local_users_is_active={}
   if postgres_schema.get("users"):
      try:
         async with postgres_client_asyncpg.transaction():
            cursor=await postgres_client_asyncpg.cursor('SELECT id,is_active FROM users ORDER BY id DESC')
            count=0
            while count < 1000000:
               batch=await cursor.fetch(10000)
               if not batch:break
               local_users_is_active.update({record['id']: record['is_active'] for record in batch})
               if False:await redis_client.mset({f"users_is_active_{record['id']}":0 if record['is_active']==0 else 1 for record in batch})
               count+=len(batch)
      except Exception as e:print(f"Error in set_users_is_active: {e}")
      users_is_active=local_users_is_active
   return None

redis_client=None
valkey_client=None
redis_pubsub=None
import redis.asyncio as redis
async def set_redis_client():
   global redis_client
   global valkey_client
   global redis_pubsub
   if redis_url:
      redis_client=redis.Redis.from_pool(redis.ConnectionPool.from_url(redis_url))
      redis_pubsub=redis_client.pubsub()
      await redis_pubsub.subscribe(channel_name)
   if valkey_url:valkey_client=redis.Redis.from_pool(redis.ConnectionPool.from_url(valkey_url))
   return None

mongodb_client=None
import motor.motor_asyncio
async def set_mongodb_client():
   global mongodb_client
   if mongodb_url:mongodb_client=motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
   return None

s3_client=None
s3_resource=None
import boto3
async def set_s3_client():
   global s3_client
   global s3_resource
   if s3_region_name:
      s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
      s3_resource=boto3.resource("s3",region_name=s3_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   return None

sns_client=None
import boto3
async def set_sns_client():
   global sns_client
   if sns_region_name:
      sns_client=boto3.client("sns",region_name=sns_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   return None

ses_client=None
import boto3
async def set_ses_client():
   global ses_client
   if ses_region_name:
      ses_client=boto3.client("ses",region_name=ses_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   return None

rabbitmq_client=None
rabbitmq_channel=None
import pika
async def set_rabbitmq_client():
   global rabbitmq_client
   global rabbitmq_channel
   if rabbitmq_url:
      rabbitmq_client=pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
      rabbitmq_channel=rabbitmq_client.channel()
      rabbitmq_channel.queue_declare(queue=channel_name)
   return None

lavinmq_client=None
lavinmq_channel=None
import pika
async def set_lavinmq_client():
   global lavinmq_client
   global lavinmq_channel
   if lavinmq_url:
      lavinmq_client=pika.BlockingConnection(pika.URLParameters(lavinmq_url))
      lavinmq_channel=lavinmq_client.channel()
      lavinmq_channel.queue_declare(queue=channel_name)
   return None

kafka_producer_client=None
kafka_consumer_client=None
from aiokafka import AIOKafkaProducer
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context
async def set_kafka_client():
   global kafka_producer_client
   global kafka_consumer_client
   if kafka_url:
      context=create_ssl_context(cafile=kafka_path_cafile,certfile=kafka_path_certfile,keyfile=kafka_path_keyfile)
      kafka_producer_client=AIOKafkaProducer(bootstrap_servers=kafka_url,security_protocol="SSL",ssl_context=context)
      kafka_consumer_client=AIOKafkaConsumer(channel_name,bootstrap_servers=kafka_url,security_protocol="SSL",ssl_context=context,enable_auto_commit=True,auto_commit_interval_ms=10000)
      await kafka_producer_client.start()
      await kafka_consumer_client.start()
   return None

#app
import sentry_sdk
if sentry_dsn:sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

from fastapi import Request,Response
import jwt,json,hashlib
def redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
   api=request.url.path
   query_param_sorted=str(dict(sorted(request.query_params.items())))
   token=request.headers.get("Authorization").split("Bearer ",1)[1] if request.headers.get("Authorization") and "Bearer " in request.headers.get("Authorization") else None
   user_id=0
   if "my/" in api:user_id=json.loads(jwt.decode(token,key_jwt,algorithms="HS256")["data"])["id"]
   key=f"{api}---{query_param_sorted}---{str(user_id)}".lower()
   if False:key=hashlib.sha256(str(key).encode()).hexdigest()
   return key

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def lifespan(app:FastAPI):
   try:
      #connect
      await set_postgres_client()
      await set_postgres_schema()
      await set_users_api_access()
      await set_users_is_active()
      await set_redis_client()
      await set_s3_client()
      await set_sns_client()
      await set_ses_client()
      await set_mongodb_client()
      await set_rabbitmq_client()
      await set_lavinmq_client()
      await set_kafka_client()
      #ratelimiter
      if redis_client:await FastAPILimiter.init(redis_client)
      #cache
      if valkey_client:FastAPICache.init(RedisBackend(valkey_client),key_builder=redis_key_builder)
      else:FastAPICache.init(RedisBackend(redis_client),key_builder=redis_key_builder)
      #disconnect
      yield
      await postgres_client.disconnect()
      await postgres_client_asyncpg.close()
      if redis_client:await redis_client.aclose()
      if valkey_client:await valkey_client.aclose()
      if rabbitmq_client and rabbitmq_channel.is_open:rabbitmq_channel.close()
      if rabbitmq_client and rabbitmq_client.is_open:rabbitmq_client.close()
      if lavinmq_client and lavinmq_channel.is_open:lavinmq_channel.close()
      if lavinmq_client and lavinmq_client.is_open:lavinmq_client.close()
      if kafka_producer_client:await kafka_producer_client.stop()
   except Exception as e:print(e.args)

from fastapi import FastAPI
app=FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

from fastapi import Request,responses
import time,traceback
from starlette.background import BackgroundTask
object_list_log_api=[]
@app.middleware("http")
async def middleware(request:Request,api_function):
   global object_list_log_api
   start=time.time()
   api=request.url.path
   token=request.headers.get("Authorization").split("Bearer ",1)[1] if request.headers.get("Authorization") and "Bearer " in request.headers.get("Authorization") else None
   request.state.user={}
   error_text=None
   try:
      #auth check
      if any(item in api for item in ["root/","my/", "private/", "admin/"]) and not token:return error("Bearer token must")
      if token:
         if "root/" in api:
            if token!=key_root:return error("token root mismatch")
         else:
            request.state.user=json.loads(jwt.decode(token,key_jwt,algorithms="HS256")["data"])
            response=await admin_check(request,api,api_id,users_api_access,postgres_client)
            if response["status"]==0:return error(response["message"])
            response=await is_active_check(request,api,users_is_active)
            if response["status"]==0:return error(response["message"])   
      #api response
      if request.query_params.get("is_background")=="1":
         body=await request.body()
         async def receive():return {"type":"http.request","body":body}
         async def api_function_new():
            request_new=Request(scope=request.scope,receive=receive)
            await api_function(request_new)
         response=responses.JSONResponse(status_code=200,content={"status":1,"message":"added in background"})
         response.background=BackgroundTask(api_function_new)
      else:response=await api_function(request)
   except Exception as e:
      print(traceback.format_exc())
      error_text=str(e.args)
      response=error(error_text)
   #log
   response_time_ms=(time.time()-start)*1000
   object={"created_by_id":request.state.user.get("id",None),"api":api,"method":request.method,"query_param":json.dumps(dict(request.query_params)),"status_code":response.status_code,"response_time_ms":response_time_ms,"description":error_text}
   object_list_log_api.append(object)
   if postgres_schema.get("log_api") and len(object_list_log_api)>=10 and request.query_params.get("is_background")!="1":
      response.background=BackgroundTask(postgres_create,"log_api",object_list_log_api,0,postgres_client,postgres_column_datatype,object_serialize)
      object_list_log_api=[]
   #final
   return response

import os,glob
for filename in []:
   router=__import__(filename).router
   app.include_router(router)
      
#api import
from fastapi import Request,UploadFile,Depends,BackgroundTasks,responses
import hashlib,datetime,json,time,os,random,httpx
from typing import Literal
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter

#index
@app.get("/")
async def index():
   return {"status":1,"message":"welcome to atom"}

#root
@app.post("/root/db-init")
async def root_db_init(request:Request):
   #param
   mode=request.query_params.get("mode")
   if not mode:return error("mode missing")
   #logic
   if mode=="default":await postgres_schema_init(postgres_client,postgres_schema_read,postgres_config)
   if mode=="custom":await postgres_schema_init(postgres_client,postgres_schema_read,await request.json())
   await set_postgres_schema()
   #final
   return {"status":1,"message":"done"}

@app.put("/root/reset-global")
async def root_reset_global():
   #logic
   await set_postgres_schema()
   await set_users_api_access()
   await set_users_is_active()
   #final
   return {"status":1,"message":"done"}

@app.put("/root/db-checklist")
async def root_db_checklist():
   #logix
   await postgres_client.execute(query="update users set is_active=1,is_deleted=null where id=1;",values={})
   #final
   return {"status":1,"message":"done"}

@app.post("/root/db-uploader")
async def root_db_uploader(request:Request):
   #param
   form_data_key,form_data_file=await form_data_read(request)
   mode=form_data_key.get("mode")
   table=form_data_key.get("table")
   is_serialize=int(form_data_key.get("is_serialize",1))
   if not mode or not table or not form_data_file:return error("mode/table/file missing")
   object_list=await file_to_object_list(form_data_file[-1])
   #logic
   if mode=="create":response=await postgres_create(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if mode=="update":response=await postgres_update(table,object_list,1,postgres_client,postgres_column_datatype,object_serialize)
   if mode=="delete":response=await postgres_delete(table,object_list,1,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.post("/root/redis-set-csv")
async def root_redis_set_csv(request:Request):
   #param
   form_data_key,form_data_file=await form_data_read(request)
   table=form_data_key.get("table")
   expiry=form_data_key.get("expiry")
   if not table or not form_data_file:return error("table/file missing")
   object_list=await file_to_object_list(form_data_file[-1])   
   #logic
   async with redis_client.pipeline(transaction=True) as pipe:
      for object in object_list:
         key=f"{table}_{object['id']}"
         if not expiry:pipe.set(key,json.dumps(object))
         else:pipe.setex(key,expiry,json.dumps(object))
      await pipe.execute()
   #final
   return {"status":1,"message":"done"}

@app.delete("/root/redis-reset")
async def root_reset_redis():
   #logic
   if redis_client:await redis_client.flushall()
   if valkey_client:await valkey_client.flushall()
   #final
   return {"status":1,"message":"done"}

@app.delete("/root/s3-url-delete")
async def root_s3_url_empty(request:Request):
   #param
   url=request.query_params.get("url")
   if not url:return error("url missing")
   #logic
   for item in url.split("---"):
      bucket,key=item.split("//",1)[1].split(".",1)[0],item.rsplit("/",1)[1]
      output=s3_resource.Object(bucket,key).delete()
   #final
   return {"status":1,"message":output}

@app.get("/root/s3-bucket-list")
async def root_s3_bucket_list():
   #logic
   output=s3_client.list_buckets()
   #final
   return {"status":1,"message":output}

@app.post("/root/s3-bucket-ops")
async def root_s3_bucket_ops(request:Request):
   #param
   mode=request.query_params.get("mode")
   bucket=request.query_params.get("bucket")
   if not mode or not bucket:return error("mode/bucket missing")
   #logic
   if mode=="create":output=s3_client.create_bucket(Bucket=bucket,CreateBucketConfiguration={'LocationConstraint':s3_region_name})
   if mode=="public":
      s3_client.put_public_access_block(Bucket=bucket,PublicAccessBlockConfiguration={'BlockPublicAcls':False,'IgnorePublicAcls':False,'BlockPublicPolicy':False,'RestrictPublicBuckets':False})
      policy='''{"Version":"2012-10-17","Statement":[{"Sid":"PublicRead","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":["arn:aws:s3:::bucket_name/*"]}]}'''
      output=s3_client.put_bucket_policy(Bucket=bucket,Policy=policy.replace("bucket_name",bucket))
   if mode=="empty":output=s3_resource.Bucket(bucket).objects.all().delete()
   if mode=="delete":output=s3_client.delete_bucket(Bucket=bucket)
   #final
   return {"status":1,"message":output}

#admin
@app.post("/admin/db-runner")
async def admin_db_runner(request:Request):
   #param
   query=(await request.json()).get("query")
   if not query:return error("query must")
   #check
   danger_word=["drop","truncate"]
   stop_word=["drop","delete","update","insert","alter","truncate","create", "rename","replace","merge","grant","revoke","execute","call","comment","set","disable","enable","lock","unlock"]
   must_word=["select"]
   for item in danger_word:
       if item in query.lower():return error(f"{item} keyword not allowed in query")
   if request.state.user["id"]!=1:
      for item in stop_word:
         if item in query.lower():return error(f"{item} keyword not allowed in query")
      for item in must_word:
         if item not in query.lower():return error(f"{item} keyword must be present in query")
   #logic
   output=await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":output}

@app.post("/admin/user-create")
async def admin_user_create(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   username=object.get("username")
   password=object.get("password")
   api_access=object.get("api_access")
   if not type or not username or not password:return error("type/username/password missing")
   password=hashlib.sha256(str(password).encode()).hexdigest()
   #check
   if type not in user_type_allowed:return error("wrong type")
   #logic
   query="insert into users (type,username,password,api_access) values (:type,:username,:password,:api_access) returning *;"
   values={"type":type,"username":username,"password":password,"api_access":api_access}
   output=await postgres_client.execute(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.put("/admin/user-update")
async def admin_user_update(request:Request):
   #param
   object=await request.json()
   object["updated_by_id"]=request.state.user["id"]
   #check
   if "id" not in object:return error ("id missing")
   if len(object)<=2:return error ("object length issue")
   if any(key in object and len(object)!=3 for key in ["password"]):return error("object length should be 2")
   #logic
   response=await postgres_update("users",[object],1,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.post("/admin/object-create")
async def admin_object_create(request:Request):
   #param
   table=request.query_params.get("table")
   is_serialize=int(request.query_params.get("is_serialize",1))
   if not table:return error("table missing")
   object=await request.json()
   object["created_by_id"]=request.state.user["id"]
   #check
   if table not in ["test"]:return error("table not allowed")
   #logic
   response=await postgres_create(table,[object],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.put("/admin/object-update")
async def admin_object_update(request:Request):
   #param
   table=request.query_params.get("table")
   is_serialize=int(request.query_params.get("is_serialize",1))
   object=await request.json()
   if postgres_schema.get(table).get("updated_by_id"):object["updated_by_id"]=request.state.user["id"]
   if not table:return error("table missing")
   #check
   if table in ["users"]:return error("table not allowed")
   if len(object)<=2:return error ("object issue")
   if "id" not in object:return error ("id missing")
   #logic
   response=await postgres_update(table,[object],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.put("/admin/ids-update")
async def admin_ids_update(request:Request):
   #param
   table=request.query_params.get("table")
   ids=request.query_params.get("ids")
   if not table or not ids:return error("table/ids must")
   object=await request.json()
   key,value=next(reversed(object.items()),(None, None))
   #check
   if table in ["users"]:return error("table not allowed")
   if len(object)!=1:return error(" object length should be 1")
   #logic
   query=f"update {table} set {key}=:value,updated_by_id=:updated_by_id where id in ({ids});"
   values={"updated_by_id":request.state.user["id"],"value":object.get(key)}
   await postgres_client.execute(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@app.delete("/admin/ids-delete")
async def admin_ids_delete(request:Request):
   #param
   table=request.query_params.get("table")
   ids=request.query_params.get("ids")
   if not table or not ids:return error("table/ids must")
   #check
   if table in ["users"]:return error("table not allowed")
   #logic
   query=f"delete from {table} where id in ({ids});"
   await postgres_client.execute(query=query,values={})
   #final
   return {"status":1,"message":"done"}

@app.get("/admin/object-read")
@cache(expire=60)
async def admin_object_read(request:Request):
   #param
   table=request.query_params.get("table")
   if not table:return error("table missing")
   object=request.query_params
   #logic
   response=await postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string)
   if response["status"]==0:return error(response["message"])
   #final
   return response

#public
output_cache_public_info={}
@app.get("/public/info")
async def public_info(request:Request):
   #param
   global output_cache_public_info
   #logic
   if output_cache_public_info and (time.time()-output_cache_public_info.get("set_at")<=100):output=output_cache_public_info.get("output")
   else:
      output={
      "set_at":time.time(),
      "postgres_schema":postgres_schema,
      "postgres_column_datatype":postgres_column_datatype,
      "api_list":[route.path for route in request.app.routes],
      "users_api_access_count":len(users_api_access),
      "users_is_active_count":len(users_is_active),
      "redis":await redis_client.info(),
      "api_id":api_id,
      "variable_size_kb":dict(sorted({f"{name} ({type(var).__name__})":sys.getsizeof(var) / 1024 for name, var in globals().items() if not name.startswith("__")}.items(), key=lambda item:item[1], reverse=True)),
      "users_count":await postgres_client.fetch_all(query="select count(*) from users where is_active is distinct from 0;",values={}),
      }
      output_cache_public_info["set_at"]=time.time()
      output_cache_public_info["output"]=output
   #final
   return {"status":1,"message":output}

@app.post("/public/otp-send-mobile-sns")
async def public_otp_send_mobile_sns(request:Request):
   #param
   object=await request.json()
   mobile=object.get("mobile")
   entity_id=object.get("entity_id")
   sender_id=object.get("sender_id")
   template_id=object.get("template_id")
   message=object.get("message")
   if not mobile:return error("mobile missing")
   #otp save
   otp=random.randint(100000,999999)
   query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;"
   values={"otp":otp,"mobile":mobile.strip().lower()}
   await postgres_client.execute(query=query,values=values)
   #logic
   if not entity_id:output=sns_client.publish(PhoneNumber=mobile,Message=str(otp))
   else:output=sns_client.publish(PhoneNumber=mobile,Message=message.replace("{otp}",str(otp)),MessageAttributes={"AWS.MM.SMS.EntityId":{"DataType":"String","StringValue":entity_id},"AWS.MM.SMS.TemplateId":{"DataType":"String","StringValue":template_id},"AWS.SNS.SMS.SenderID":{"DataType":"String","StringValue":sender_id},"AWS.SNS.SMS.SMSType":{"DataType":"String","StringValue":"Transactional"}})
   #final
   return {"status":1,"message":output}

@app.post("/public/otp-send-email-ses")
async def public_otp_send_email_ses(request:Request):
   #param
   object=await request.json()
   email=object.get("email")
   if not email:return error("email missing")
   #otp save
   otp=random.randint(100000,999999)
   query="insert into otp (otp,email) values (:otp,:email) returning *;"
   values={"otp":otp,"email":email.strip().lower()}
   await postgres_client.fetch_all(query=query,values=values)
   #logic
   to,title,body=[email],"otp from atom",str(otp)
   ses_client.send_email(Source=ses_sender_email,Destination={"ToAddresses":to},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":body}}})
   #final
   return {"status":1,"message":"done"}

@app.post("/public/object-create")
async def public_object_create(request:Request):
   #param
   table=request.query_params.get("table")
   is_serialize=int(request.query_params.get("is_serialize",1))
   if not table:return error("table missing")
   object=await request.json()
   #check
   if table not in ["test"]:return error("table not allowed")
   #logic
   response=await postgres_create(table,[object],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.get("/public/object-read")
@cache(expire=100)
async def public_object_read(request:Request):
   #param
   table=request.query_params.get("table")
   creator_data=request.query_params.get("creator_data")
   if not table:return error("table missing")
   object=request.query_params
   #check
   if table not in ["test"]:return error("table not allowed")
   #logic
   if postgres_client_read:response=await postgres_read(table,object,postgres_client_read,postgres_column_datatype,object_serialize,create_where_string)
   else:response=await postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string)
   if response["status"]==0:return error(response["message"])
   object_list=response["message"]
   #add creator data
   if creator_data:
      response=await add_creator_data(postgres_client,object_list,creator_data)
      if response["status"]==0:return response
      object_list=response["message"]
   #final
   return {"status":1,"message":object_list}

#private
@app.post("/private/file-upload-s3-presigned")
async def private_file_upload_s3_presigned(request:Request):
   #param
   bucket=request.query_params.get("bucket")
   key=request.query_params.get("key")
   if not bucket or not key:return error("bucket/key missing")
   expiry_sec,size_kb=1000,100
   #check
   if "." not in key:return error("extension must")
   #logic
   output=s3_client.generate_presigned_post(Bucket=bucket,Key=key,ExpiresIn=expiry_sec,Conditions=[['content-length-range',1,size_kb*1024]])
   for k,v in output["fields"].items():output[k]=v
   del output["fields"]
   output["url_final"]=f"https://{bucket}.s3.{s3_region_name}.amazonaws.com/{key}"
   #final
   return {"status":1,"message":output}

@app.post("/private/file-upload-s3-direct")
async def private_file_upload_s3_direct(request:Request):
   #param
   form_data_key,form_data_file=await form_data_read(request)
   bucket=form_data_key.get("bucket")
   key=form_data_key.get("key")
   if not bucket or not key or not form_data_file:return error("bucket/key/file missing")
   key_list=None if key=="uuid" else key.split("---")
   #logic
   response=await s3_file_upload(s3_client,s3_region_name,bucket,key_list,form_data_file)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.get("/private/object-read")
@cache(expire=100)
async def private_object_read(request:Request):
   #param
   table=request.query_params.get("table")
   if not table:return error("table missing")
   object=request.query_params
   #check
   if table not in ["test"]:return error("table not allowed")
   #logic
   response=await postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.get("/private/workseeker-read")
@cache(expire=100)
async def private_workseeker_read(request:Request):
   #pagination
   order,limit,page=request.query_params.get("order","id desc"),int(request.query_params.get("limit",100)),int(request.query_params.get("page",1))
   #filter
   work_profile_id=int(request.query_params.get("work_profile_id")) if request.query_params.get("work_profile_id") else None
   experience_min=int(request.query_params.get("experience_min")) if request.query_params.get("experience_min") else None
   experience_max=int(request.query_params.get("experience_max")) if request.query_params.get("experience_max") else None
   skill=f"%{request.query_params.get('skill')}%" if request.query_params.get('skill') else None
   #logic
   query=f'''
   select * from workseeker where
   (work_profile_id=:work_profile_id or :work_profile_id is null) and
   (experience >= :experience_min or :experience_min is null) and
   (experience <= :experience_max or :experience_max is null) and
   (skill ilike :skill or :skill is null)
   order by {order} limit {limit} offset {(page-1)*limit};
   '''
   values={
   "work_profile_id":work_profile_id,
   "experience_min":experience_min,"experience_max":experience_max,
   "skill":skill
   }
   output=await postgres_client.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#auth
@app.post("/auth/signup-username-password",dependencies=[Depends(RateLimiter(times=100,seconds=1))])
async def auth_signup_username_password(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   username=object.get("username")
   password=object.get("password")
   if not type or not username or not password:return error("type/username/password missing")
   password=hashlib.sha256(str(password).encode()).hexdigest()
   #check
   if is_signup==0:return error("signup disabled")
   if type not in user_type_allowed:return error("wrong type")
   #logic
   query="insert into users (type,username,password) values (:type,:username,:password) returning *;"
   values={"type":type,"username":username,"password":password}
   output=await postgres_client.execute(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/auth/login-password-username")
async def auth_login_password_username(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   username=object.get("username")
   password=object.get("password")
   if not type or not username or not password:return error("type/username/password missing")
   password=hashlib.sha256(str(password).encode()).hexdigest()
   #logic
   query=f"select * from users where type=:type and username=:username and password=:password order by id desc limit 1;"
   values={"type":type,"username":username,"password":password}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return error("user not found")
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.post("/auth/login-password-email")
async def auth_login_password_email(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   email=object.get("email")
   password=object.get("password")
   if not type or not email or not password:return error("type/email/password missing")
   password=hashlib.sha256(str(password).encode()).hexdigest()
   #logic
   query=f"select * from users where type=:type and email=:email and password=:password order by id desc limit 1;"
   values={"type":type,"email":email,"password":password}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return error("user not found")
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.post("/auth/login-password-mobile")
async def auth_login_password_mobile(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   mobile=object.get("mobile")
   password=object.get("password")
   if not type or not mobile or not password:return error("type/mobile/password missing")
   password=hashlib.sha256(str(password).encode()).hexdigest()
   #logic
   query=f"select * from users where type=:type and mobile=:mobile and password=:password order by id desc limit 1;"
   values={"type":type,"mobile":mobile,"password":password}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return error("user not found")
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.post("/auth/login-otp-email")
async def auth_login_otp_email(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   email=object.get("email")
   otp=object.get("otp")
   if not type or not email or not otp:return error("type/email/otp missing")
   #check
   if type not in user_type_allowed:return error("wrong type")
   #otp verify
   response=await verify_otp(postgres_client,otp,email,None)
   if response["status"]==0:return error(response["message"])
   #logic
   query=f"select * from users where type=:type and email=:email order by id desc limit 1;"
   values={"type":type,"email":email}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:
      query=f"insert into users (type,email) values (:type,:email) returning *;"
      values={"type":type,"email":email}
      output=await postgres_client.fetch_all(query=query,values=values)
      user=output[0] if output else None
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.post("/auth/login-otp-mobile")
async def auth_login_otp_mobile(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   mobile=object.get("mobile")
   otp=object.get("otp")
   if not type or not mobile or not otp:return error("type/mobile/otp missing")
   #check
   if type not in user_type_allowed:return error("wrong type")
   #otp verify
   response=await verify_otp(postgres_client,otp,None,mobile)
   if response["status"]==0:return error(response["message"])
   #logic
   query=f"select * from users where type=:type and mobile=:mobile order by id desc limit 1;"
   values={"type":type,"mobile":mobile}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:
      query=f"insert into users (type,mobile) values (:type,:mobile) returning *;"
      values={"type":type,"mobile":mobile}
      output=await postgres_client.fetch_all(query=query,values=values)
      user=output[0] if output else None
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.post("/auth/login-oauth-google")
async def auth_login_oauth_google(request:Request):
   #param
   object=await request.json()
   type=object.get("type")
   google_token=object.get("google_token")
   if not type or not google_token:return error("type/google_token missing")
   #check
   if type not in user_type_allowed:return error("wrong type")
   #verify
   response=verify_google_token(google_client_id,google_token)
   if response["status"]==0:return error(response["message"])
   google_user=response["message"]
   #logic
   query=f"select * from users where type=:type and google_id=:google_id order by id desc limit 1;"
   values={"type":type,"google_id":google_user["sub"]}
   output=await postgres_client.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:
      query=f"insert into users (type,google_id,google_data) values (:type,:google_id,:google_data) returning *;"
      values={"type":type,"google_id":google_user["sub"],"google_data":json.dumps(google_user)}
      output=await postgres_client.fetch_all(query=query,values=values)
      user=output[0] if output else None
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

#my
@app.get("/my/profile")
async def my_profile(request:Request,background:BackgroundTasks):
   #logic
   response=await request_user_read(request)
   if response["status"]==0:return error(response["message"])
   user=response["message"]
   #background
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"id":request.state.user["id"],"last_active_at":datetime.datetime.now()}
   background.add_task(postgres_client.execute,query,values)
   #final
   return {"status":1,"message":user}

@app.get("/my/token-refresh")
async def my_token_refresh(request:Request):
   #logic
   response=await request_user_read(request)
   if response["status"]==0:return error(response["message"])
   user=response["message"]
   token=await token_create(key_jwt,user)
   #final
   return {"status":1,"message":token}

@app.delete("/my/account-delete-soft")
async def my_account_delete_soft(request:Request):
   #check
   response=await request_user_read(request)
   if response["status"]==0:return error(response["message"])
   user=response["message"]
   print(user)
   if user["api_access"]:return error("user not allowed as you have api_access")
   #logic
   async with postgres_client.transaction():
      await postgres_client.execute(query="update message set is_deleted=1 where created_by_id=:user_id or user_id=:user_id;",values={"user_id":request.state.user["id"]})
      await postgres_client.execute(query="update users set is_deleted=1 where id=:id;",values={"id":request.state.user["id"]})
   #final
   return {"status":1,"message":"done"}

@app.delete("/my/account-delete-hard")
async def my_account_delete_hard(request:Request):
   #check
   response=await request_user_read(request)
   if response["status"]==0:return error(response["message"])
   user=response["message"]
   if user["api_access"]:return error("user not allowed as you have api_access")
   #logic
   async with postgres_client.transaction():
      await postgres_client.execute(query="delete from report_user where created_by_id=:user_id or user_id=:user_id;",values={"user_id":request.state.user["id"]})
      await postgres_client.execute(query="delete from bookmark_workseeker where created_by_id=:user_id",values={"user_id":request.state.user["id"]})
      await postgres_client.execute(query="delete from message where created_by_id=:user_id or user_id=:user_id;",values={"user_id":request.state.user["id"]})
      await postgres_client.execute(query="delete from users where id=:id;",values={"id":request.state.user["id"]})
   #final
   return {"status":1,"message":"done"}

@app.post("/my/object-create")
async def my_object_create(request:Request):
   #param
   table=request.query_params.get("table")
   is_serialize=int(request.query_params.get("is_serialize",1))
   queue=request.query_params.get("queue")
   if not table:return error("table missing")
   object=await request.json()
   object["created_by_id"]=request.state.user["id"]
   data={"mode":"create","table":table,"object":object,"is_serialize":is_serialize}
   #check
   if table not in ["test","message","report_user","bookmark_workseeker","workseeker"]:return error("table not allowed")
   if len(object)<=1:return error ("object issue")
   if any(key in column_disabled_non_admin for key in object):return error(" object key not allowed")
   #logic
   if not queue:
      response=await postgres_create(table,[object],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
      if response["status"]==0:return error(response["message"])
      output=response["message"]
   elif queue=="redis":output=await redis_client.publish(channel_name,json.dumps(data))
   elif queue=="rabbitmq":output=rabbitmq_channel.basic_publish(exchange='',routing_key=channel_name,body=json.dumps(data))
   elif queue=="lavinmq":output=lavinmq_channel.basic_publish(exchange='',routing_key=channel_name,body=json.dumps(data))
   elif queue=="kafka":output=await kafka_producer_client.send_and_wait(channel_name,json.dumps(data,indent=2).encode('utf-8'),partition=0)
   elif "mongodb" in queue:
      mongodb_database_name=queue.split('_')[1]
      mongodb_database_client=mongodb_client[mongodb_database_name]
      output=await mongodb_database_client[table].insert_many([object])
      output=str(output)
   #final
   return {"status":1,"message":output}

@app.get("/my/object-read")
@cache(expire=60)
async def my_object_read(request:Request):
   #param
   table=request.query_params.get("table")
   if not table:return error("table missing")
   object=dict(request.query_params)
   object["created_by_id"]=f"=,{request.state.user['id']}"
   #check
   if table in ["users"]:return error("table not allowed")
   #logic
   response=await postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string)
   if response["status"]==0:return error(response["message"])
   object_list=response["message"]
   #final
   return {"status":1,"message":object_list}

@app.put("/my/user-update")
async def my_user_update(request:Request):
   #param
   object=await request.json()
   object["updated_by_id"]=request.state.user["id"]
   otp=int(request.query_params.get("otp",0))
   #check
   if "id" not in object:return error ("id missing")
   if object["id"]!=request.state.user["id"]:return error ("wrong id")
   if len(object)<=2:return error ("object length issue")
   if any(key in column_disabled_non_admin for key in object):return error(" object key not allowed")
   if any(key in object and len(object)!=3 for key in ["password","email","mobile"]):return error("object length should be 2")
   if any(key in object and not otp for key in ["email","mobile"]):return error("otp missing")
   #otp verify
   if otp:
      email,mobile=object.get("email"),object.get("mobile")
      response=await verify_otp(postgres_client,otp,email,mobile)
      if response["status"]==0:return error(response["message"])
   #logic
   response=await postgres_update("users",[object],1,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.put("/my/object-update")
async def my_object_update(request:Request):
   #param
   table=request.query_params.get("table")
   is_serialize=int(request.query_params.get("is_serialize",1))
   object=await request.json()
   object["updated_by_id"]=request.state.user["id"]
   if not table:return error("table missing")
   #check
   if table in ["users"]:return error("table not allowed")
   if "id" not in object:return error ("id missing")
   if len(object)<=2:return error ("object null issue")
   if any(key in column_disabled_non_admin for key in object):return error(" object key not allowed")
   #logic
   response=await postgres_update_self(table,[object],is_serialize,postgres_client,postgres_column_datatype,object_serialize,request.state.user["id"])
   if response["status"]==0:return error(response["message"])
   #final
   return response

@app.put("/my/ids-update")
async def my_ids_update(request:Request):
   #param
   table=request.query_params.get("table")
   ids=request.query_params.get("ids")
   if not table or not ids:return error("table/ids must")
   object=await request.json()
   key,value=next(reversed(object.items()),(None, None))
   #check
   if table in ["users"]:return error("table not allowed")
   if any(key in column_disabled_non_admin for key in object):return error(" object key not allowed")
   if len(object)!=1:return error(" object length should be 1")
   #logic
   query=f"update {table} set {key}=:value,updated_by_id=:updated_by_id where id in ({ids}) and created_by_id=:created_by_id;"
   values={"created_by_id":request.state.user["id"],"updated_by_id":request.state.user["id"],"value":object.get(key)}
   await postgres_client.execute(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@app.delete("/my/object-delete-any")
async def my_object_delete_any(request:Request):
   #param
   table=request.query_params.get("table")
   if not table:return error("table missing")
   object=dict(request.query_params)
   object["created_by_id"]=f"=,{request.state.user['id']}"
   #check
   if table not in ["test","report_user","bookmark_workseeker"]:return error("table not allowed")
   #create where
   response=await create_where_string(object,object_serialize,postgres_column_datatype)
   if response["status"]==0:return error(response["message"])
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   query=f"delete from {table} {where_string};"
   await postgres_client.fetch_all(query=query,values=where_value)
   #final
   return {"status":1,"message":"done"}

@app.delete("/my/ids-delete")
async def my_ids_delete(request:Request):
   #param
   table=request.query_params.get("table")
   ids=request.query_params.get("ids")
   if not table or not ids:return error("table/ids must")
   #check
   if table not in ["test","report_user","bookmark_workseeker"]:return error("table not allowed")
   #logic
   query=f"delete from {table} where id in ({ids}) and created_by_id=:created_by_id;"
   values={"created_by_id":request.state.user["id"]}
   await postgres_client.execute(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@app.get("/my/parent-read")
async def my_parent_read(request:Request):
   #param
   order,limit,page=request.query_params.get("order","id desc"),int(request.query_params.get("limit",100)),int(request.query_params.get("page",1))
   table=request.query_params.get("table")
   table_parent=table.split('_',1)[-1]
   column=f"{table_parent}_id"
   if table_parent=="user":table_parent="users"
   if not table:return error("table missing")
   #logic
   query=f'''
   with 
   x as (select {column} from {table} where created_by_id=:created_by_id order by {order} limit {limit} offset {(page-1)*limit}) 
   select ct.* from x left join {table_parent}  as ct on x.{column}=ct.id;
   '''
   values={"created_by_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":object_list}

#message
@app.get("/my/message-inbox")
async def my_message_inbox(request:Request):
   #param
   mode=request.query_params.get("mode")
   order,limit,page=request.query_params.get("order","id desc"),int(request.query_params.get("limit",100)),int(request.query_params.get("page",1))
   #logic
   if not mode:query=f'''with x as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),y as (select max(id) as id from x group by unique_id),z as (select m.* from y left join message as m on y.id=m.id) select * from z order by {order} limit {limit} offset {(page-1)*limit};'''
   elif mode=="unread":query=f'''with x as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),y as (select max(id) as id from x group by unique_id),z as (select m.* from y left join message as m on y.id=m.id),a as (select * from z where user_id=:user_id and is_read!=1 is null) select * from a order by {order} limit {limit} offset {(page-1)*limit};'''
   values={"created_by_id":request.state.user["id"],"user_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":object_list}

@app.get("/my/message-received")
async def my_message_received(request:Request,background:BackgroundTasks):
   #param
   mode=request.query_params.get("mode")
   order,limit,page=request.query_params.get("order","id desc"),int(request.query_params.get("limit",100)),int(request.query_params.get("page",1))
   #logic
   if not mode:query=f"select * from message where user_id=:user_id order by {order} limit {limit} offset {(page-1)*limit};"
   elif mode=="unread":query=f"select * from message where user_id=:user_id and is_read is distinct from 1 order by {order} limit {limit} offset {(page-1)*limit};"
   values={"user_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=values)
   #background
   query=f"update message set is_read=1,updated_by_id=:updated_by_id where id in ({','.join([str(item['id']) for item in object_list])});"
   values={"updated_by_id":request.state.user["id"]}
   background.add_task(postgres_client.execute,query,values)
   #final
   return {"status":1,"message":object_list}

@app.get("/my/message-thread")
async def my_message_thread(request:Request,background:BackgroundTasks):
   #param
   order,limit,page=request.query_params.get("order","id desc"),int(request.query_params.get("limit",100)),int(request.query_params.get("page",1))
   user_id=int(request.query_params.get("user_id",0))
   if not user_id:return error("user_id missing")
   #logic
   query=f"select * from message where ((created_by_id=:user_1 and user_id=:user_2) or (created_by_id=:user_2 and user_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
   values={"user_1":request.state.user["id"],"user_2":user_id}
   object_list=await postgres_client.fetch_all(query=query,values=values)
   #background
   query="update message set is_read=1,updated_by_id=:updated_by_id where created_by_id=:created_by_id and user_id=:user_id;"
   values={"created_by_id":user_id,"user_id":request.state.user["id"],"updated_by_id":request.state.user["id"]}
   background.add_task(postgres_client.execute,query,values)
   #final
   return {"status":1,"message":object_list}

@app.delete("/my/message-delete")
async def my_message_delete(request:Request):
   #param
   mode=request.query_params.get("mode")
   id=int(request.query_params.get("id",0))
   if not mode:return error("mode missing")
   if mode=="single" and not id:return error("id missing")
   #logic
   if mode=="single":output=await postgres_client.execute(query="delete from message where id=:id and (created_by_id=:user_id or user_id=:user_id);",values={"id":int(id),"user_id":request.state.user["id"]})
   if mode=="created":output=await postgres_client.execute(query="delete from message where created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
   if mode=="received":output=await postgres_client.execute(query="delete from message where user_id=:user_id;",values={"user_id":request.state.user["id"]})
   if mode=="all":output=await postgres_client.execute(query="delete from message where (created_by_id=:user_id or user_id=:user_id);",values={"user_id":request.state.user["id"]})
   #final
   return {"status":1,"message":output}

#mode
import sys
mode=sys.argv

#fastapi
import asyncio,uvicorn
async def main_fastapi():
   config=uvicorn.Config(app,host="0.0.0.0",port=8000,log_level="info",reload=True)
   server=uvicorn.Server(config)
   await server.serve()
if __name__=="__main__" and len(mode)==1:
   try:asyncio.run(main_fastapi())
   except KeyboardInterrupt:print("exit")
   
#nest
import nest_asyncio
nest_asyncio.apply()

#redis
import asyncio,json
async def main_redis():
   await set_postgres_client()
   await set_postgres_schema()
   await set_redis_client()
   try:
      async for message in redis_pubsub.listen():
         if message["type"]=="message" and message["channel"]==b'ch1':
            data=json.loads(message['data'])
            try:
               if data["mode"]=="create":response=await postgres_create(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize)
               if data["mode"]=="update":response=await postgres_update(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize)
               print(response)
            except Exception as e:
               print(e.args)
   except asyncio.CancelledError:print("subscription cancelled")
   finally:
      await postgres_client.disconnect()
      await redis_pubsub.unsubscribe("postgres_crud")
      await redis_client.aclose()
if __name__ == "__main__" and len(mode)>1 and mode[1]=="redis":
    try:asyncio.run(main_redis())
    except KeyboardInterrupt:print("exit")

#kafka
import asyncio,json
async def main_kafka():
   await set_postgres_client()
   await set_postgres_schema()
   await set_kafka_client()
   try:
      async for message in kafka_consumer_client:
         if message.topic==channel_name:
            data=json.loads(message.value.decode('utf-8'))
            try:
               if data["mode"]=="create":response=await postgres_create(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize)   
               if data["mode"]=="update":response=await postgres_update(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize)
               print(response)
            except Exception as e:
               print(e.args)
   except asyncio.CancelledError:print("subscription cancelled")
   finally:
      await postgres_client.disconnect()
      await kafka_consumer_client.stop()
if __name__ == "__main__" and len(mode)>1 and mode[1]=="kafka":
    try:asyncio.run(main_kafka())
    except KeyboardInterrupt:print("exit")

#aqmp callback
def aqmp_callback(ch,method,properties,body):
   data=json.loads(body)
   loop=asyncio.get_event_loop()
   try:
      if data["mode"]=="create":response=loop.run_until_complete(postgres_create(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize))
      if data["mode"]=="update":response=loop.run_until_complete(postgres_update(data["table"],[data["object"]],data["is_serialize"],postgres_client,postgres_column_datatype,object_serialize))
      print(response)
   except Exception as e:
      print(e.args)
   return None

#rabbitmq
import asyncio,json
async def main_rabbitmq():
   await set_postgres_client()
   await set_postgres_schema()
   await set_rabbitmq_client()
   try:
      rabbitmq_channel.basic_consume(channel_name,aqmp_callback,auto_ack=True)
      rabbitmq_channel.start_consuming()
   except KeyboardInterrupt:
      await postgres_client.disconnect()
      rabbitmq_channel.close()
      rabbitmq_client.close()
if __name__ == "__main__" and len(mode)>1 and mode[1]=="rabbitmq":
    try:asyncio.run(main_rabbitmq())
    except KeyboardInterrupt:print("exit")

#lavinmq
import asyncio,json
async def main_lavinmq():
   await set_postgres_client()
   await set_postgres_schema()
   await set_lavinmq_client()
   try:
      lavinmq_channel.basic_consume(channel_name,aqmp_callback,auto_ack=True)
      lavinmq_channel.start_consuming()
   except KeyboardInterrupt:
      await postgres_client.disconnect()
      lavinmq_channel.close()
      lavinmq_client.close()
if __name__ == "__main__" and len(mode)>1 and mode[1]=="lavinmq":
    try:asyncio.run(main_lavinmq())
    except KeyboardInterrupt:print("exit")