#function
async def postgres_create(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list:return {"status":0,"message":"object null issue"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   column_insert_list=list(object_list[0].keys())
   query=f"insert into {table} ({','.join(column_insert_list)}) values ({','.join([':'+item for item in column_insert_list])}) on conflict do nothing returning *;"
   if len(object_list)==1:output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_read(table,object,postgres_client,postgres_column_datatype,object_serialize,create_where_string,add_creator_data,add_action_count,table_id):
   order,limit,page=object.get("order","id desc"),int(object.get("limit",100)),int(object.get("page",1))
   creator_data,action_count,location_filter=object.get("creator_data",None),object.get("action_count",None),object.get("location_filter",None)
   response=await create_where_string(postgres_column_datatype,object_serialize,object)
   if response["status"]==0:return response
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   if location_filter:
      long,lat,min_meter,max_meter=float(location_filter.split(",")[0]),float(location_filter.split(",")[1]),int(location_filter.split(",")[2]),int(location_filter.split(",")[3])
      query=f'''with x as (select * from {table} {where_string}),y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x) select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {(page-1)*limit};'''
   object_list=await postgres_client.fetch_all(query=query,values=where_value)
   if creator_data:
      response=await add_creator_data(postgres_client,object_list,creator_data)
      if response["status"]==0:return response
      object_list=response["message"]
   if action_count:
      for action_table in action_count.split(","):
         response=await add_action_count(postgres_client,table_id,action_table,table,object_list)
         if response["status"]==0:return response
         object_list=response["message"]
   return {"status":1,"message":object_list}

async def postgres_update(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list:return {"status":0,"message":"object null issue"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   column_update_list=[*object_list[0]]
   column_update_list.remove("id")
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_update_list])} where id=:id returning *;"
   if len(object_list)==1:output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def postgres_delete(table,object_list,is_serialize,postgres_client,postgres_column_datatype,object_serialize):
   if not object_list:return {"status":0,"message":"object null issue"}
   if is_serialize:
      response=await object_serialize(postgres_column_datatype,object_list)
      if response["status"]==0:return response
      object_list=response["message"]
   query=f"delete from {table} where id=:id;"
   if len(object_list)==1:output=await postgres_client.execute(query=query,values=object_list[0])
   else:
      async with postgres_client.transaction():output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

async def add_creator_data(postgres_client,object_list,user_key):
   if not object_list:return {"status":1,"message": object_list}
   object_list=[dict(object) for object in object_list]
   created_by_ids={str(object["created_by_id"]) for object in object_list if object.get("created_by_id")}
   if created_by_ids:
      query=f"SELECT * FROM users WHERE id IN ({','.join(created_by_ids)});"
      users={user["id"]:dict(user) for user in await postgres_client.fetch_all(query=query, values={})}
   for object in object_list:
      if object["created_by_id"] in users:
         for key in user_key.split(","):object[f"creator_{key}"]=users[object["created_by_id"]][key]
      else:
         for key in user_key.split(","):object[f"creator_{key}"]=None    
   return {"status":1,"message":object_list}

async def add_action_count(postgres_client,table_id,action,object_table,object_list):
   if not object_list:return {"status":1,"message":object_list}
   key_name=f"{action}_count"
   object_list=[dict(item)|{key_name:0} for item in object_list]
   parent_ids_list=[str(item["id"]) for item in object_list if item["id"]]
   parent_ids_string=",".join(parent_ids_list)
   if parent_ids_string:
      query=f"select parent_id,count(*) from {action} where parent_table=:parent_table and parent_id in ({parent_ids_string}) group by parent_id;"
      query_param={"parent_table":table_id.get(object_table,0)}
      object_list_action=await postgres_client.fetch_all(query=query,values=query_param)
      for x in object_list:
         for y in object_list_action:
               if x["id"]==y["parent_id"]:
                  x[key_name]=y["count"]
                  break
   return {"status":1,"message":object_list}

async def ownership_check(postgres_client,table,id,user_id):
   if table=="users":
      if id!=user_id:return {"status":0,"message":"object ownership issue"}
   if table!="users":
      output=await postgres_client.fetch_all(query=f"select created_by_id from {table} where id=:id;",values={"id":id})
      if not output:return {"status":0,"message":"no object"}
      if output[0]["created_by_id"]!=user_id:return {"status":0,"message":"object ownership issue"}
   return {"status":1,"message":"done"}

async def verify_otp(postgres_client,otp,email,mobile):
   if not otp:return {"status":0,"message":"otp must"}
   if email:output=await postgres_client.fetch_all(query="select otp from otp where created_at>current_timestamp-interval '10 minutes' and email=:email order by id desc limit 1;",values={"email":email})
   if mobile:output=await postgres_client.fetch_all(query="select otp from otp where created_at>current_timestamp-interval '10 minutes' and mobile=:mobile order by id desc limit 1;",values={"mobile":mobile})
   if not output:return {"status":0,"message":"otp not found"}
   if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
   return {"status":1,"message":"done"}

import hashlib,datetime,json
async def object_serialize(postgres_column_datatype, object_list):
   for index, object in enumerate(object_list):
      for k, v in object.items():
         datatype = postgres_column_datatype.get(k)
         if not datatype:return{"status":0,"message":f"column {k} is not in postgres schema"}
         if not v: object_list[index][k] = None
         elif "text" in datatype: object_list[index][k] = str(v)
         elif "int" in datatype: object_list[index][k] = int(v)
         elif k in ["password", "google_id"]: object_list[index][k] = hashlib.sha256(v.encode()).hexdigest()
         elif datatype == "numeric": object_list[index][k] = round(float(v), 3)
         elif "time" in datatype or datatype == "date": object_list[index][k] = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
         elif datatype=="jsonb": object_list[index][k] = json.dumps(v)
         elif datatype=="ARRAY": object_list[index][k] = v.split(",")
   return {"status":1,"message":object_list}

async def create_where_string(postgres_column_datatype,object_serialize,object):
   object={k:v for k,v in object.items() if k in postgres_column_datatype}
   object={k:v for k,v in object.items() if k not in ["metadata","location","table","order","limit","page"]}
   object_key_operator={k:v.split(',',1)[0] for k,v in object.items()}
   object_key_value={k:v.split(',',1)[1] for k,v in object.items()}
   column_read_list=[*object]
   where_column_single_list=[f"({column} {object_key_operator[column]} :{column} or :{column} is null)" for column in column_read_list]
   where_column_joined=' and '.join(where_column_single_list)
   where_string=f"where {where_column_joined}" if where_column_joined else ""
   response=await object_serialize(postgres_column_datatype,[object_key_value])
   if response["status"]==0:return response
   where_value=response["message"][0]
   return {"status":1,"message":[where_string,where_value]}

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

async def postgres_schema_init(postgres_client,postgres_schema_read,config):
   #extension
   await postgres_client.fetch_all(query="create extension if not exists postgis;",values={})
   #table
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      is_table=postgres_schema.get(table,{})
      if not is_table:await postgres_client.execute(query=f"create table if not exists {table} (id bigint primary key generated always as identity not null);",values={})
   #column
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         is_column=postgres_schema.get(table,{}).get(column_name,{})
         if not is_column:await postgres_client.execute(query=f"alter table {table} add column if not exists {column_name} {column_datatype};",values={})
   #nullable
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         is_null=postgres_schema.get(table,{}).get(column_name,{}).get("is_null",None)
         if column_is_mandatory=="0" and is_null==0:await postgres_client.execute(query=f"alter table {table} alter column {column_name} drop not null;",values={})
         if column_is_mandatory=="1" and is_null==1:await postgres_client.execute(query=f"alter table {table} alter column {column_name} set not null;",values={})
   #index
   postgres_schema=await postgres_schema_read(postgres_client)
   for table,column_list in config["table"].items():
      for column in column_list:
         column_name,column_datatype,column_is_mandatory,column_index_type=column.split("-")
         index_name=f"index_{table}_{column_name}"
         is_index=postgres_schema.get(table,{}).get(column_name,{}).get("is_index",None)
         if column_index_type=="0" and is_index==1:await postgres_client.execute(query=f"drop index if exists {index_name};",values={})
         if column_index_type!="0" and is_index==0:await postgres_client.execute(query=f"create index concurrently if not exists {index_name} on {table} using {column_index_type} ({column_name});",values={})
   #query
   constraint_name_list={object["constraint_name"] for object in (await postgres_client.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={}))}
   for query in config["query"].values():
      if "add constraint" in query and query.split()[5] in constraint_name_list:continue
      await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":"done"}

async def postgres_schema_read(postgres_client):
   postgres_schema={}
   query='''
   WITH t AS (SELECT * FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'), 
   c AS (
   SELECT table_name, column_name, data_type, 
   CASE WHEN is_nullable = 'YES' THEN 1 ELSE 0 END AS is_nullable, 
   column_default 
   FROM information_schema.columns 
   WHERE table_schema='public'
   ), 
   i AS (
   SELECT t.relname::text AS table_name, a.attname AS column_name, 
   CASE WHEN idx.indisprimary OR idx.indisunique OR idx.indisvalid THEN 1 ELSE 0 END AS is_index
   FROM pg_attribute a
   JOIN pg_class t ON a.attrelid = t.oid
   JOIN pg_namespace ns ON t.relnamespace = ns.oid
   LEFT JOIN pg_index idx ON a.attrelid = idx.indrelid AND a.attnum = ANY(idx.indkey)
   WHERE ns.nspname = 'public' AND a.attnum > 0 AND t.relkind = 'r'
   )
   SELECT t.table_name as table, c.column_name as column, c.data_type as datatype,c.column_default as default, c.is_nullable as is_null, COALESCE(i.is_index, 0) AS is_index 
   FROM t 
   LEFT JOIN c ON t.table_name = c.table_name 
   LEFT JOIN i ON t.table_name = i.table_name AND c.column_name = i.column_name;
   '''
   output=await postgres_client.fetch_all(query=query,values={})
   for object in output:
      table,column=object["table"],object["column"]
      column_data={"datatype": object["datatype"],"default": object["default"],"is_null": object["is_null"],"is_index": object["is_index"]}
      if table not in postgres_schema:postgres_schema[table]={}
      postgres_schema[table][column]=column_data
   return postgres_schema

import csv,io
async def file_to_object_list(file):
   content=await file.read()
   csv_text=content.decode("utf-8")
   reader=csv.DictReader(io.StringIO(csv_text))
   object_list=[row for row in reader]
   await file.close()
   return object_list

async def read_body_form(request):
   body_form=await request.form()
   body_form_key={key:value for key,value in body_form.items() if isinstance(value,str)}
   body_form_file=[file for key,value in body_form.items() for file in body_form.getlist(key)  if key not in body_form_key and file.filename]
   return body_form_key,body_form_file

from fastapi import responses
def error(message):
   return responses.JSONResponse(status_code=400,content={"status":0,"message":message})

#env
import os,json
from dotenv import load_dotenv
load_dotenv()
postgres_database_url=os.getenv("postgres_database_url")
redis_server_url=os.getenv("redis_server_url")
key_root=os.getenv("key_root")
key_jwt=os.getenv("key_jwt")
sentry_dsn=os.getenv("sentry_dsn")
rabbitmq_server_url=os.getenv("rabbitmq_server_url")
lavinmq_server_url=os.getenv("lavinmq_server_url")
kafka_path_cafile=os.getenv("kafka_path_cafile")
kafka_path_certfile=os.getenv("kafka_path_certfile")
kafka_path_keyfile=os.getenv("kafka_path_keyfile")
kafka_server_url=os.getenv("kafka_server_url")
aws_access_key_id=os.getenv("aws_access_key_id")
aws_secret_access_key=os.getenv("aws_secret_access_key")
s3_region_name=os.getenv("s3_region_name")
sns_region_name=os.getenv("sns_region_name")
ses_region_name=os.getenv("ses_region_name")
mongodb_cluster_url=os.getenv("mongodb_cluster_url")
channel_name=os.getenv("channel_name","ch1")
log_api_reset_count=int(os.getenv("log_api_reset_count",10))
token_expire_sec=int(os.getenv("token_expire_sec",1000000000000))
max_ids_length_delete=int(os.getenv("max_ids_length_delete",3))
table_id=json.loads(os.getenv("table_id",'{"users":1,"post":2,"atom":3,"action_comment":4}'))
is_account_delete_hard=int(os.getenv("is_account_delete_hard",0))
is_index_html=int(os.getenv("is_index_html",0))

#globals
log_api_object_list=[]
postgres_config={
"table":{
"human":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_active-smallint-0-btree",
"is_protected-smallint-0-btree",
"is_deleted-smallint-0-btree",
"type-text-0-btree",
"name-text-0-0",
"email-text-0-0",
"mobile-text-0-0",
"city-text-0-0",
"experience-numeric(10,1)-0-0",
"link_url-text-0-0",
"work_profile-text-0-0",
"skill-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"rating-numeric(10,3)-0-btree"
],
"test":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"type-text-0-btree",
"title-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"link_url-text-0-0",
"tag-text-0-0"
],
"atom":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"type-text-1-btree",
"title-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"link_url-text-0-0",
"tag-text-0-0",
"parent_table-smallint-0-btree",
"parent_id-bigint-0-btree",
"rating-numeric(10,3)-0-0"
],
"project":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_protected-smallint-0-btree",
"is_deleted-smallint-0-btree",
"type-text-1-btree",
"title-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"link_url-text-0-0",
"tag-text-0-0"
],
"users":[
"created_at-timestamptz-0-0",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_active-smallint-0-btree",
"is_protected-smallint-0-btree",
"is_deleted-smallint-0-btree",
"type-text-0-btree",
"username-text-0-0",
"password-text-0-btree",
"location-geography(POINT)-0-gist",
"metadata-jsonb-0-0",
"google_id-text-0-btree",
"last_active_at-timestamptz-0-0",
"date_of_birth-date-0-0",
"email-text-0-btree",
"mobile-text-0-btree",
"name-text-0-0",
"city-text-0-0",
"api_access-text-0-btree",
"rating-numeric(10,3)-0-0"
],
"post":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"is_active-smallint-0-btree",
"is_protected-smallint-0-btree",
"type-text-0-0","title-text-0-0",
"description-text-0-0",
"file_url-text-0-0",
"link_url-text-0-0",
"tag-text-0-0",
"location-geography(POINT)-0-0",
"metadata-jsonb-0-0",
"rating-numeric(10,3)-0-0"
],
"message":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-1-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"user_id-bigint-1-btree",
"description-text-1-0",
"is_read-smallint-0-btree"
],
"helpdesk":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-0-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"status-text-0-0",
"remark-text-0-0",
"type-text-0-0",
"description-text-1-0",
"email-text-0-btree"
],
"otp":[
"created_at-timestamptz-1-brin",
"otp-integer-1-0",
"email-text-0-btree",
"mobile-text-0-btree"
],
"log_api":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-0-0",
"method-text-0-0",
"api-text-0-0",
"status_code-smallint-0-0",
"response_time_ms-numeric(1000,3)-0-0",
"is_deleted-smallint-0-btree"
],
"log_password":[
"created_at-timestamptz-1-0",
"user_id-bigint-0-0",
"password-text-0-0",
"is_deleted-smallint-0-btree"
],
"action_like":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree"
],
"action_bookmark":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree"
],
"action_report":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree"
],
"action_block":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree"
],
"action_follow":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree"
],
"action_rating":[
"created_at-timestamptz-1-0",
"created_by_id-bigint-1-btree",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree",
"rating-numeric(10,3)-1-0"
],
"action_comment":[
"created_at-timestamptz-0-0",
"created_by_id-bigint-1-btree",
"updated_at-timestamptz-0-0",
"updated_by_id-bigint-0-0",
"is_deleted-smallint-0-btree",
"parent_table-smallint-1-btree",
"parent_id-bigint-1-btree",
"description-text-1-0"
]
},
"query":{
"delete_disable_bulk_function":"create or replace function function_delete_disable_bulk() returns trigger language plpgsql as $$declare n bigint := tg_argv[0]; begin if (select count(*) from deleted_rows) <= n is not true then raise exception 'cant delete more than % rows', n; end if; return old; end;$$;",
"delete_disable_bulk_users":"create or replace trigger trigger_delete_disable_bulk_users after delete on users referencing old table as deleted_rows for each statement execute procedure function_delete_disable_bulk(1);",
"delete_disable_bulk_human":"create or replace trigger trigger_delete_disable_bulk_human after delete on human referencing old table as deleted_rows for each statement execute procedure function_delete_disable_bulk(1);",
"default_created_at":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name='created_at' AND table_schema = 'public') LOOP EXECUTE FORMAT('ALTER TABLE ONLY %I ALTER COLUMN created_at SET DEFAULT NOW();', tbl.table_name); END LOOP; END $$;",
"default_updated_at_1":"create or replace function function_set_updated_at_now() returns trigger as $$ begin new.updated_at=now(); return new; end; $$ language 'plpgsql';",
"default_updated_at_2":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema = 'public') LOOP EXECUTE FORMAT('CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_%I BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION function_set_updated_at_now();', tbl.table_name, tbl.table_name); END LOOP; END $$;",
"default_is_protected_users":"ALTER TABLE users ALTER COLUMN is_protected SET DEFAULT 1;",
"default_is_protected_project":"ALTER TABLE project ALTER COLUMN is_protected SET DEFAULT 1;",
"default_is_protected_human":"ALTER TABLE human ALTER COLUMN is_protected SET DEFAULT 1;",
"rule_is_protected":"DO $$ DECLARE tbl RECORD; BEGIN FOR tbl IN (SELECT table_name FROM information_schema.columns WHERE column_name='is_protected' AND table_schema='public') LOOP EXECUTE FORMAT('CREATE OR REPLACE RULE rule_protect_%I AS ON DELETE TO %I WHERE OLD.is_protected = 1 DO INSTEAD NOTHING;', tbl.table_name, tbl.table_name); END LOOP; END $$;",
"root_user_1":"insert into users (username,password,api_access) values ('atom','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','1,2,3,4,5,6,7,8,9,10') on conflict do nothing;",
"root_user_2":"create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;",
"log_password_1":"CREATE OR REPLACE FUNCTION function_log_password_change() RETURNS TRIGGER LANGUAGE PLPGSQL AS $$ BEGIN IF OLD.password <> NEW.password THEN INSERT INTO log_password(user_id,password) VALUES(OLD.id,OLD.password); END IF; RETURN NEW; END; $$;",
"log_password_2":"CREATE OR REPLACE TRIGGER trigger_log_password_change AFTER UPDATE ON users FOR EACH ROW WHEN (OLD.password IS DISTINCT FROM NEW.password) EXECUTE FUNCTION function_log_password_change();",
"unique_users_username":"alter table users add constraint constraint_unique_users_username unique (username);",
"unique_acton_like":"alter table action_like add constraint constraint_unique_action_like_cpp unique (created_by_id,parent_table,parent_id);",
"unique_acton_bookmark":"alter table action_bookmark add constraint constraint_unique_action_bookmark_cpp unique (created_by_id,parent_table,parent_id);",
"unique_acton_report":"alter table action_report add constraint constraint_unique_action_report_cpp unique (created_by_id,parent_table,parent_id);",
"unique_acton_block":"alter table action_block add constraint constraint_unique_action_block_cpp unique (created_by_id,parent_table,parent_id);",
"unique_acton_follow":"alter table action_follow add constraint constraint_unique_action_follow_cpp unique (created_by_id,parent_table,parent_id);"
}
}
api_id={
"/admin/object-read":1,
"/admin/object-update":2,
"/admin/delete-ids-soft":3,
"/admin/delete-ids-hard":4,
"/admin/db-runner":5,
}

#setters
postgres_client=None
from databases import Database
async def set_postgres_client():
   global postgres_client
   postgres_client=Database(os.getenv("postgres_database_url"),min_size=1,max_size=100)
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

user_api_access={}
async def set_user_api_access():
   global user_api_access
   user_api_access={}
   if postgres_schema.get("users",{}).get("api_access",None):
         output=await postgres_client.fetch_all(query="select id,api_access from users where api_access is not null limit 10000",values={})
         user_api_access={object["id"]:[int(item) for item in object["api_access"].split(",")] for object in output if len(object["api_access"])>=1}
   return None

project_data={}
async def set_project_data():
   global project_data
   project_data={}
   if postgres_schema.get("project",None):
      output=await postgres_client.fetch_all(query="select * from project limit 10000;",values={})
      for object in output:
         if object["type"] not in project_data:project_data[object["type"]]=[object]
         else:project_data[object["type"]]+=[object]
   return None

redis_client=None
redis_pubsub=None
import redis.asyncio as redis
async def set_redis_client():
   global redis_client
   global redis_pubsub
   if redis_server_url:
      redis_client=redis.Redis.from_pool(redis.ConnectionPool.from_url(os.getenv("redis_server_url")))
      redis_pubsub=redis_client.pubsub()
      await redis_pubsub.subscribe(channel_name)
   return None

mongodb_client=None
import motor.motor_asyncio
async def set_mongodb_client():
   global mongodb_client
   if mongodb_cluster_url:mongodb_client=motor.motor_asyncio.AsyncIOMotorClient(mongodb_cluster_url)
   return None

s3_client=None
s3_resource=None
import boto3
async def set_s3_client():
   global s3_client,s3_resource
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
   if rabbitmq_server_url:
      rabbitmq_client=pika.BlockingConnection(pika.URLParameters(os.getenv("rabbitmq_server_url")))
      rabbitmq_channel=rabbitmq_client.channel()
      rabbitmq_channel.queue_declare(queue=channel_name)
   return None

lavinmq_client=None
lavinmq_channel=None
import pika
async def set_lavinmq_client():
   global lavinmq_client
   global lavinmq_channel
   if lavinmq_server_url:
      lavinmq_client=pika.BlockingConnection(pika.URLParameters(os.getenv("lavinmq_server_url")))
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
   if kafka_server_url:
      context=create_ssl_context(cafile=os.getenv("kafka_path_cafile"),certfile=os.getenv("kafka_path_certfile"),keyfile=os.getenv("kafka_path_keyfile"))
      kafka_producer_client=AIOKafkaProducer(bootstrap_servers=os.getenv("kafka_server_url"),security_protocol="SSL",ssl_context=context)
      kafka_consumer_client=AIOKafkaConsumer(channel_name,bootstrap_servers=os.getenv("kafka_server_url"),security_protocol="SSL",ssl_context=context,enable_auto_commit=True,auto_commit_interval_ms=10000)
      await kafka_producer_client.start()
      await kafka_consumer_client.start()
   return None

#sentry
import sentry_sdk
if sentry_dsn:
   sentry_sdk.init(dsn=sentry_dsn,traces_sample_rate=1.0,profiles_sample_rate=1.0)

#redis key builder
from fastapi import Request,Response
import jwt,json
def redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
   api=request.url.path
   query_param=str(dict(sorted(request.query_params.items())))
   token=request.headers.get("Authorization").split("Bearer ",1)[1] if request.headers.get("Authorization") and "Bearer " in request.headers.get("Authorization") else None
   user_id=0
   if token and "my/" in api:user_id=json.loads(jwt.decode(token,os.getenv("key_jwt"),algorithms="HS256")["data"])["id"]
   key=f"{api}---{query_param}---{str(user_id)}"
   return key

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def lifespan(app:FastAPI):
   await set_postgres_client()
   await set_postgres_schema()
   await set_user_api_access()
   await set_project_data()
   await set_redis_client()
   await set_s3_client()
   await set_sns_client()
   await set_ses_client()
   await set_mongodb_client()
   await set_rabbitmq_client()
   await set_lavinmq_client()
   await set_kafka_client()
   if redis_server_url:
      await FastAPILimiter.init(redis_client)
      FastAPICache.init(RedisBackend(redis_client),key_builder=redis_key_builder)
   yield
   try:
      await postgres_client.disconnect()
      if redis_server_url:await redis_client.aclose()
      if rabbitmq_server_url and rabbitmq_channel.is_open:rabbitmq_channel.close()
      if rabbitmq_server_url and rabbitmq_client.is_open:rabbitmq_client.close()
      if lavinmq_server_url and lavinmq_channel.is_open:lavinmq_channel.close()
      if lavinmq_server_url and lavinmq_client.is_open:lavinmq_client.close()
      if kafka_server_url:await kafka_producer_client.stop()
   except Exception as e:print(e.args)

#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan)

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request,responses
import time,traceback
from starlette.background import BackgroundTask
@app.middleware("http")
async def middleware(request:Request,api_function):
   start=time.time()
   method=request.method
   api=request.url.path
   query_param=dict(request.query_params)
   body=await request.body()
   token=request.headers.get("Authorization").split("Bearer ",1)[1] if request.headers.get("Authorization") and "Bearer " in request.headers.get("Authorization") else None
   try:
      #auth
      user={}
      if any(item in api for item in ["root/","my/", "private/", "admin/"]) and not token:return error("Bearer token must")
      if token:
         if "root/" in api:
            if token!=key_root:return error("key root mismatch")
         else:
            user=json.loads(jwt.decode(token,key_jwt,algorithms="HS256")["data"])
            if not user.get("id",None):return error("user_id not in token")
            if "admin/" in api:
               if not api_id.get(api):return error("api id mapping not added")
               if api_id[api] not in user_api_access.get(user["id"],[]):return error("api access denied")
      request.state.user=user
      #api response background
      if query_param.get("is_background",None)=="1":
         async def receive():return {"type":"http.request","body":body}
         async def api_function_new():
            request_new=Request(scope=request.scope,receive=receive)
            await api_function(request_new)
         response=responses.JSONResponse(status_code=200,content={"status":1,"message":"added in background"})
         response.background=BackgroundTask(api_function_new)
      #api response direct
      else:
         #api response
         response=await api_function(request)
         #api log
         if postgres_schema.get("log_api"):
            global log_api_object_list
            object={"created_by_id":user.get("id",None),"method":method,"api":api,"status_code":response.status_code,"response_time_ms":(time.time()-start)*1000}
            log_api_object_list.append(object)
            if len(log_api_object_list)>=log_api_reset_count:
               response.background=BackgroundTask(postgres_create,"log_api",log_api_object_list,0,postgres_client,postgres_column_datatype,object_serialize)
               log_api_object_list=[]
   #exception
   except Exception as e:
      print(traceback.format_exc())
      return error(str(e.args))
   #final
   return response

#router
import os,glob
current_directory_path=os.path.dirname(os.path.realpath(__file__))
current_directory_file_path_list=glob.glob(f"{current_directory_path}/*")
current_directory_file_name_list=[item.rsplit("/",1)[-1] for item in current_directory_file_path_list]
current_directory_file_name_list_without_extension=[item.split(".")[0] for item in current_directory_file_name_list]
for item in current_directory_file_name_list_without_extension:
   if "api_" in item:
      router=__import__(item).router
      app.include_router(router)
      
#api import
from fastapi import Request,UploadFile,Depends,BackgroundTasks,responses
import hashlib,datetime,json,time,jwt,os,random
from typing import Literal
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter

#api
@app.get("/")
async def root():
   return {"status":1,"message":"welcome to atom"} if is_index_html==0 else responses.FileResponse("index.html")

@app.post("/root/db-init")
async def root_db_init(request:Request):
   query_param=dict(request.query_params)
   mode=query_param.get("mode",None)
   if not mode:return error("mode missing")
   if mode=="default":config=postgres_config
   if mode=="custom":config=await request.json()
   response=await postgres_schema_init(postgres_client,postgres_schema_read,config)
   await set_postgres_schema()
   return response

@app.put("/root/db-checklist")
async def root_db_checklist():
   await postgres_client.execute(query="update users set is_protected=1 where type is not null;",values={})
   return {"status":1,"message":"done"}

@app.delete("/root/db-clean")
async def root_db_clean():
   await postgres_client.execute(query="delete from log_api where created_at<now()-interval '100 days'",values={})
   await postgres_client.execute(query="delete from log_password where created_at<now()-interval '1000 days'",values={})
   await postgres_client.execute(query="delete from otp where created_at<now()-interval '100 days'",values={})
   await postgres_client.execute(query="delete from message where created_at<now()-interval '1000 days'",values={})
   [await postgres_client.execute(query=f"delete from {table} where created_by_id not in (select id from users);",values={}) for table in [*postgres_schema] if "action_" in table]
   [await postgres_client.execute(query=f"delete from {table} where parent_table={table_id.get(parent_table,0)} and parent_id not in (select id from {parent_table});",values={}) for table in [*postgres_schema] for parent_table in [*table_id] if "action_" in table]
   [await postgres_client.execute(query=f"delete from {table} where parent_table not in ({','.join([str(id) for id in table_id.values()])});",values={}) for table in [*postgres_schema] if "action_" in table]
   return {"status":1,"message":"done"}

@app.post("/root/db-uploader")
async def root_db_uploader(request:Request):
   body_form_key,body_form_file=await read_body_form(request)
   mode,table=body_form_key.get("mode",None),body_form_key.get("table",None)
   if not mode or not table:return error("body form mode/table missing")
   if not body_form_file:return error("body form file missing")
   object_list=await file_to_object_list(body_form_file[-1])
   if mode=="create":response=await postgres_create(table,object_list,1,postgres_client,postgres_column_datatype,object_serialize)
   if mode=="update":response=await postgres_update(table,object_list,1,postgres_client,postgres_column_datatype,object_serialize)
   if mode=="delete":response=await postgres_delete(table,object_list,1,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   return response

@app.post("/root/db-runner")
async def root_db_runner(request:Request):
   body_json=await request.json()
   query=body_json.get("query",None)
   if not query:return error("body json query missing")
   output=[]
   async with postgres_client.transaction():
      for query in query.split("---"):
         result=await postgres_client.fetch_all(query=query,values={})
         output.append(result)
   return {"status":1,"message":output}

@app.put("/root/reset-global")
async def root_reset_global():
   await set_postgres_schema()
   await set_project_data()
   await set_user_api_access()
   return {"status":1,"message":"done"}

@app.post("/root/redis-set-object")
async def root_redis_set_object(request:Request):
   query_param=dict(request.query_params)
   key=query_param.get("key",None)
   expiry=query_param.get("expiry",None)
   if not key:return error("query param key missing")
   body_json=await request.json()
   if not expiry:output=await redis_client.set(key,json.dumps(body_json))
   else:output=await redis_client.setex(key,expiry,json.dumps(body_json))
   return {"status":1,"message":output}

@app.post("/root/redis-set-csv")
async def root_redis_set_csv(request:Request):
   body_form_key,body_form_file=await read_body_form(request)
   table,expiry=body_form_key.get("table",None),body_form_key.get("expiry",None)
   if not table:return error("body form table missing")
   if not body_form_file:return error("body form file missing")
   object_list=await file_to_object_list(body_form_file[-1])
   async with redis_client.pipeline(transaction=True) as pipe:
      for object in object_list:
         key=f"{table}_{object['id']}"
         if not expiry:pipe.set(key,json.dumps(object))
         else:pipe.setex(key,expiry,json.dumps(object))
      await pipe.execute()
   return {"status":1,"message":"done"}

@app.delete("/root/redis-reset")
async def root_reset_redis():
   await redis_client.flushall()
   return {"status":1,"message":"done"}

@app.get("/root/s3-bucket-list")
async def root_s3_bucket_list():
   output=s3_client.list_buckets()
   return {"status":1,"message":output}

@app.post("/root/s3-bucket-create")
async def root_s3_bucket_create(request:Request):
   body_json=await request.json()
   bucket=body_json.get("bucket",None)
   if not bucket:return error("body json bucket missing")
   output=s3_client.create_bucket(Bucket=bucket,CreateBucketConfiguration={'LocationConstraint':s3_region_name})
   return {"status":1,"message":output}

@app.put("/root/s3-bucket-public")
async def root_s3_bucket_public(request:Request):
   body_json=await request.json()
   bucket=body_json.get("bucket",None)
   if not bucket:return error("body json bucket missing")
   s3_client.put_public_access_block(Bucket=bucket,PublicAccessBlockConfiguration={'BlockPublicAcls':False,'IgnorePublicAcls':False,'BlockPublicPolicy':False,'RestrictPublicBuckets':False})
   policy='''{"Version":"2012-10-17","Statement":[{"Sid":"PublicRead","Effect":"Allow","Principal": "*","Action": "s3:GetObject","Resource":["arn:aws:s3:::bucket_name/*"]}]}'''
   output=s3_client.put_bucket_policy(Bucket=bucket,Policy=policy.replace("bucket_name",bucket))
   return {"status":1,"message":output}

@app.delete("/root/s3-bucket-empty")
async def root_s3_bucket_empty(request:Request):
   body_json=await request.json()
   bucket=body_json.get("bucket",None)
   if not bucket:return error("body json bucket missing")
   output=s3_resource.Bucket(bucket).objects.all().delete()
   return {"status":1,"message":output}

@app.delete("/root/s3-bucket-delete")
async def root_s3_bucket_empty(request:Request):
   body_json=await request.json()
   bucket=body_json.get("bucket",None)
   if not bucket:return error("body json bucket missing")
   output=s3_client.delete_bucket(Bucket=bucket)
   return {"status":1,"message":output}

@app.delete("/root/s3-url-delete")
async def root_s3_url_empty(request:Request):
   body_json=await request.json()
   url=body_json.get("url",None)
   if not url:return error("body json url missing")
   for item in url.split("---"):
      bucket,key=item.split("//",1)[1].split(".",1)[0],item.rsplit("/",1)[1]
      output=s3_resource.Object(bucket,key).delete()
   return {"status":1,"message":output}

@app.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def auth_signup(request:Request):
   body_json=await request.json()
   username,password=body_json.get("username",None),body_json.get("password",None)
   if not username or not password:return error("body json username/password missing")
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(str(password).encode()).hexdigest()}
   output=await postgres_client.execute(query=query,values=query_param)
   return {"status":1,"message":output}

@app.post("/auth/login")
async def auth_login(request:Request):
   body_json=await request.json()
   username,password=body_json.get("username",None),body_json.get("password",None)
   if not username or not password:return error("body json username/password missing")
   output=await postgres_client.fetch_all(query="select id from users where username=:username and password=:password order by id desc limit 1;",values={"username":username,"password":hashlib.sha256(str(password).encode()).hexdigest()})
   if not output:return error("no user")
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.post("/auth/login-google")
async def auth_login_google(request:Request):
   body_json=await request.json()
   google_id=body_json.get("google_id",None)
   if not google_id:return error("body json google_id missing")
   output=await postgres_client.fetch_all(query="select id from users where google_id=:google_id order by id desc limit 1;",values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()})
   if not output:output=await postgres_client.fetch_all(query="insert into users (google_id) values (:google_id) returning *;",values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()})
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.post("/auth/login-otp-email")
async def auth_login_otp_email(request:Request):
   body_json=await request.json()
   email,otp=body_json.get("email",None),body_json.get("otp",None)
   if not email or not otp:return error("body json email/otp missing")
   response=await verify_otp(postgres_client,otp,email,None)
   if response["status"]==0:return error(response["message"])
   output=await postgres_client.fetch_all(query="select id from users where email=:email order by id desc limit 1;",values={"email":email})
   if not output:output=await postgres_client.fetch_all(query="insert into users (email) values (:email) returning *;",values={"email":email})
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.post("/auth/login-otp-mobile")
async def auth_login_otp_mobile(request:Request):
   body_json=await request.json()
   mobile,otp=body_json.get("mobile",None),body_json.get("otp",None)
   if not mobile or not otp:return error("body json mobile/otp missing")
   response=await verify_otp(postgres_client,otp,None,mobile)
   if response["status"]==0:return error(response["message"])
   output=await postgres_client.fetch_all(query="select id from users where mobile=:mobile order by id desc limit 1;",values={"mobile":mobile})
   if not output:output=await postgres_client.fetch_all(query="insert into users (mobile) values (:mobile) returning *;",values={"mobile":mobile})
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.post("/auth/login-password-email")
async def auth_login_password_email(request:Request):
   body_json=await request.json()
   email,password=body_json.get("email",None),body_json.get("password",None)
   if not email or not password:return error("body json email/password missing")
   output=await postgres_client.fetch_all(query="select * from users where email=:email and password=:password order by id desc limit 1;",values={"email":email,"password":hashlib.sha256(str(password).encode()).hexdigest()})
   if not output:return error("no user")
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.post("/auth/login-password-mobile")
async def auth_login_password_mobile(request:Request):
   body_json=await request.json()
   mobile,password=body_json.get("mobile",None),body_json.get("password",None)
   if not mobile or not password:return error("body json mobile/password missing")
   output=await postgres_client.fetch_all(query="select * from users where mobile=:mobile and password=:password order by id desc limit 1;",values={"mobile":mobile,"password":hashlib.sha256(str(password).encode()).hexdigest()})
   if not output:return error("no user")
   user=output[0] if output else None
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.get("/my/profile")
@cache(expire=60)
async def my_profile(request:Request,background:BackgroundTasks):
   column="*"
   query_param=dict(request.query_params)
   if query_param.get("column"):column=query_param.get("column")
   user=await postgres_client.fetch_all(query=f"select {column} from users where id=:id;",values={"id":request.state.user["id"]})
   if not user:return error("no user")
   user=dict(user[0])
   if user["is_active"]!=0:user["is_active"]=1
   background.add_task(postgres_client.execute,query="update users set last_active_at=:last_active_at where id=:id",values={"id":request.state.user["id"],"last_active_at":datetime.datetime.now()})
   return {"status":1,"message":user}

@app.get("/my/token-refresh")
async def my_token_refresh(request:Request):
   token=jwt.encode({"exp":time.time()+token_expire_sec,"data":json.dumps({"id":request.state.user["id"]},default=str)},key_jwt)
   return {"status":1,"message":token}

@app.delete("/my/account-delete-soft")
async def my_account_delete_soft(request:Request):
   user=await postgres_client.fetch_all(query="select * from users where id=:id;",values={"id":request.state.user["id"]})
   if not user:return error("no user")
   if user[0]["api_access"]:return {"status":1,"message":"admin cant be deleted"}
   async with postgres_client.transaction():
      for table,column in postgres_schema.items():
         if table not in ["users"]:
            if column.get("created_by_id",None):await postgres_client.execute(query=f"update {table} set is_deleted=1 where created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
            if column.get("user_id",None):await postgres_client.execute(query=f"update {table} set is_deleted=1 where user_id=:user_id;",values={"user_id":request.state.user["id"]})
            if column.get("parent_table",None):await postgres_client.execute(query=f"update {table} set is_deleted=1 where parent_table={table_id.get('users')} and parent_id=:parent_id;",values={"parent_id":request.state.user["id"]})
      output=await postgres_client.execute(query="update users set is_deleted=1 where id=:id and type is null;",values={"id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.delete("/my/account-delete-hard")
async def my_account_delete_hard(request:Request):
   if is_account_delete_hard==0:return {"status":1,"message":f"account delete hard not allowed"}
   user=await postgres_client.fetch_all(query="select * from users where id=:id;",values={"id":request.state.user["id"]})
   if not user:return error("no user")
   if user[0]["api_access"]:return {"status":1,"message":"admin cant be deleted"}
   async with postgres_client.transaction():
      for table,column in postgres_schema.items():
         if table not in ["users","human"]:
            if column.get("created_by_id",None):await postgres_client.execute(query=f"delete from {table} where created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
            if column.get("user_id",None):await postgres_client.execute(query=f"delete from {table} where user_id=:user_id;",values={"user_id":request.state.user["id"]})
            if column.get("parent_table",None):await postgres_client.execute(query=f"delete from {table} where parent_table={table_id.get('users')} and parent_id=:parent_id;",values={"parent_id":request.state.user["id"]})
      await postgres_client.execute(query="update users set is_protected=null where id=:id and type is null;",values={"id":request.state.user["id"]})
      output=await postgres_client.execute(query="delete from users where id=:id and type is null;",values={"id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.get("/my/message-inbox")
async def my_message_inbox(request:Request):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   mode=query_param.get("mode",None)
   query=f'''with x as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),y as (select max(id) as id from x group by unique_id),z as (select m.* from y left join message as m on y.id=m.id) select * from z order by {order} limit {limit} offset {(page-1)*limit};'''
   if mode=="unread":query=f'''with x as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),y as (select max(id) as id from x group by unique_id),z as (select m.* from y left join message as m on y.id=m.id),a as (select * from z where user_id=:user_id and is_read!=1 is null) select * from a order by {order} limit {limit} offset {(page-1)*limit};'''
   query_param={"created_by_id":request.state.user["id"],"user_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   return {"status":1,"message":object_list}

@app.get("/my/message-received")
async def my_message_received(request:Request,background:BackgroundTasks):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   mode=query_param.get("mode",None)
   query=f"select * from message where user_id=:user_id order by {order} limit {limit} offset {(page-1)*limit};"
   if mode=="unread":query=f"select * from message where user_id=:user_id and is_read is distinct from 1 order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   background.add_task(postgres_client.execute,query=f"update message set is_read=1,updated_by_id=:updated_by_id where id in ({','.join([str(item['id']) for item in object_list])});",values={"updated_by_id":request.state.user["id"]})
   return {"status":1,"message":object_list}

@app.get("/my/message-thread")
async def my_message_thread(request:Request,background:BackgroundTasks):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   user_id=query_param.get("user_id",None)
   if not user_id:return error("query param user_id missing")
   user_id=int(user_id)
   query=f"select * from message where ((created_by_id=:user_1 and user_id=:user_2) or (created_by_id=:user_2 and user_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":request.state.user["id"],"user_2":user_id}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   background.add_task(postgres_client.execute,query="update message set is_read=1,updated_by_id=:updated_by_id where created_by_id=:created_by_id and user_id=:user_id;",values={"created_by_id":user_id,"user_id":request.state.user["id"],"updated_by_id":request.state.user["id"]})
   return {"status":1,"message":object_list}

@app.delete("/my/message-delete-single")
async def my_message_delete_single(request:Request):
   query_param=dict(request.query_params)
   id=query_param.get("id",None)
   if not id:return error("query param id missing")
   output=await postgres_client.execute(query="delete from message where id=:id and (created_by_id=:user_id or user_id=:user_id);",values={"id":int(id),"user_id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.delete("/my/message-delete-created")
async def my_message_delete_created(request:Request):
   output=await postgres_client.execute(query="delete from message where created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.delete("/my/message-delete-received")
async def my_message_delete_received(request:Request):
   output=await postgres_client.execute(query="delete from message where user_id=:user_id;",values={"user_id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.delete("/my/message-delete-all")
async def my_message_delete_all(request:Request):
   output=await postgres_client.execute(query="delete from message where (created_by_id=:user_id or user_id=:user_id);",values={"user_id":request.state.user["id"]})
   return {"status":1,"message":output}

@app.get("/my/action-parent-read")
async def my_action_parent_read(request:Request):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   table,parent_table,action_count=query_param.get("table",None),query_param.get("parent_table",None),query_param.get("action_count",None)
   if not table or not parent_table:return error("query param table/parent_table missing")
   query=f'''with x as (select parent_id from {table} where created_by_id=:created_by_id and parent_table={table_id.get(parent_table,0)} order by {order} limit {limit} offset {(page-1)*limit}) select pt.* from x left join {parent_table} as pt on x.parent_id=pt.id;'''
   query_param={"created_by_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   if action_count:
      for action_table in action_count.split(","):
         response=await add_action_count(postgres_client,table_id,action_table,parent_table,object_list)
         if response["status"]==0:return response
         object_list=response["message"]
   return {"status":1,"message":object_list}

@app.get("/my/action-parent-check")
async def my_action_parent_check(request:Request):
   query_param=dict(request.query_params)
   table,parent_table,parent_ids=query_param.get("table",None),query_param.get("parent_table",None),query_param.get("parent_ids",None)
   if not table or not parent_table or not parent_ids:return error("query param table/parent_table/parent_ids missing")
   query=f"select parent_id from {table} where parent_id in ({parent_ids}) and parent_table=:parent_table and created_by_id=:created_by_id;"
   query_param={"parent_table":table_id.get(parent_table,0),"created_by_id":request.state.user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   parent_ids_output=[item["parent_id"] for item in output if item["parent_id"]]
   parent_ids_input=parent_ids.split(",")
   parent_ids_input=[int(item) for item in parent_ids_input]
   output={item:1 if item in parent_ids_output else 0 for item in parent_ids_input}
   return {"status":1,"message":output}

@app.delete("/my/action-parent-delete")
async def my_action_parent_delete(request:Request):
   query_param=dict(request.query_params)
   table,parent_table,parent_id=query_param.get("table",None),query_param.get("parent_table",None),query_param.get("parent_id",None)
   if not table or not parent_table or not parent_id:return error("body json table/parent_table/parent_id missing")
   if "action_" not in table:return error("table not allowed")
   await postgres_client.fetch_all(query=f"delete from {table} where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;",values={"created_by_id":request.state.user["id"],"parent_table":table_id.get(parent_table,0),"parent_id":int(parent_id)})
   return {"status":1,"message":"done"}

@app.get("/my/action-on-me-creator-read")
async def my_action_on_me_creator_read(request:Request):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   query=f'''with x as (select * from {table} where parent_table=:parent_table),y as (select created_by_id from x where parent_id=:parent_id group by created_by_id order by max(id) desc limit {limit} offset {(page-1)*limit}) select u.id,u.username from y left join users as u on y.created_by_id=u.id;'''
   query_param={"parent_table":table_id.get('users',0),"parent_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   return {"status":1,"message":object_list}

@app.get("/my/action-on-me-creator-read-mutual")
async def my_action_on_me_creator_read_mutual(request:Request):
   query_param=dict(request.query_params)
   order,limit,page=query_param.get("order","id desc"),int(query_param.get("limit",100)),int(query_param.get("page",1))
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   query=f'''with x as (select * from {table} where parent_table=:parent_table),y as (select created_by_id from {table} where created_by_id in (select parent_id from x where created_by_id=:created_by_id) and parent_id=:parent_id group by created_by_id order by max(id) desc limit {limit} offset {(page-1)*limit}) select u.id,u.username from y left join users as u on y.created_by_id=u.id;'''
   query_param={"parent_table":table_id.get('users',0),"parent_id":request.state.user["id"],"created_by_id":request.state.user["id"]}
   object_list=await postgres_client.fetch_all(query=query,values=query_param)
   return {"status":1,"message":object_list}

@app.post("/my/object-create")
async def my_object_create(request:Request):
   query_param=dict(request.query_params)
   table,is_serialize,queue=query_param.get("table",None),int(query_param.get("is_serialize",1)),query_param.get("queue",None)
   if not table:return error("query param table missing")
   if table in ["users","spatial_ref_sys","otp","log_api","log_password"]:return error("table not allowed")
   body_json=await request.json()
   if not body_json:return error("body missing")
   if body_json.get("parent_table") and body_json.get("parent_table") not in list(table_id.values()):return error("wrong parent_table")
   if any(k in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_deleted","password","google_id","otp"] for k in body_json):return error("key not allowed")
   body_json["created_by_id"]=request.state.user["id"]
   if not queue:
      response=await postgres_create(table,[body_json],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
      if response["status"]==0:return error(response["message"])
      output=response["message"]
   if queue:
      data={"mode":"create","table":table,"object":body_json,"is_serialize":is_serialize}
      if queue=="redis":output=await redis_client.publish(channel_name,json.dumps(data))
      if queue=="rabbitmq":output=rabbitmq_channel.basic_publish(exchange='',routing_key=channel_name,body=json.dumps(data))
      if queue=="lavinmq":output=lavinmq_channel.basic_publish(exchange='',routing_key=channel_name,body=json.dumps(data))
      if queue=="kafka":output=await kafka_producer_client.send_and_wait(channel_name,json.dumps(data,indent=2).encode('utf-8'),partition=0)
      if "mongodb" in queue:
         mongodb_database_name=queue.split("_")[1]
         mongodb_database_client=mongodb_client[mongodb_database_name]
         output=await mongodb_database_client[table].insert_many([body_json])
         output=str(output)
   return {"status":1,"message":output}

@app.post("/public/object-create")
async def public_object_create(request:Request):
   query_param=dict(request.query_params)
   table,is_serialize=query_param.get("table",None),int(query_param.get("is_serialize",1))
   if not table:return error("query param table missing")
   if table not in ["test","helpdesk","human"]:return error("table not allowed")
   body_json=await request.json()
   if body_json.get("parent_table") and body_json.get("parent_table") not in list(table_id.values()):return error("wrong parent_table")
   response=await postgres_create(table,[body_json],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   return response

@app.get("/my/object-read")
@cache(expire=60)
async def my_object_read(request:Request):
   query_param=dict(request.query_params)
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   query_param["created_by_id"]=f"=,{request.state.user['id']}"
   response=await postgres_read(table,query_param,postgres_client,postgres_column_datatype,object_serialize,create_where_string,add_creator_data,add_action_count,table_id)
   if response["status"]==0:return error(response["message"])
   return response

@app.get("/admin/object-read")
@cache(expire=60)
async def admin_object_read(request:Request):
   query_param=dict(request.query_params)
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   response=await postgres_read(table,query_param,postgres_client,postgres_column_datatype,object_serialize,create_where_string,add_creator_data,add_action_count,table_id)
   if response["status"]==0:return error(response["message"])
   return response

@app.get("/public/object-read")
@cache(expire=60)
async def public_object_read(request:Request):
   query_param=dict(request.query_params)
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   if table not in ["users","post","atom"]:return error("table not allowed")
   response=await postgres_read(table,query_param,postgres_client,postgres_column_datatype,object_serialize,create_where_string,add_creator_data,add_action_count,table_id)
   if response["status"]==0:return error(response["message"])
   return response

@app.put("/my/object-update")
async def my_object_update(request:Request):
   query_param=dict(request.query_params)
   table,is_serialize,otp=query_param.get("table",None),int(query_param.get("is_serialize",1)),int(query_param.get("otp",0))
   if not table:return error("query param table missing")
   body_json=await request.json()
   if body_json.get("parent_table") and body_json.get("parent_table") not in list(table_id.values()):return error("wrong parent_table")
   if any(k in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp"] for k in body_json):return error("key not allowed")     
   if "password" in body_json:is_serialize=1
   body_json["updated_by_id"]=request.state.user["id"]
   response=await ownership_check(postgres_client,table,int(body_json["id"]),request.state.user["id"])
   if response["status"]==0:return error(response["message"])
   email,mobile=body_json.get("email",None),body_json.get("mobile",None)
   if email and mobile:return error("email/mobile both not allowed together")
   if table=="users" and (email or mobile):
      response=await verify_otp(postgres_client,otp,email,mobile)
      if response["status"]==0:return error(response["message"])
   response=await postgres_update(table,[body_json],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   return response

@app.put("/admin/object-update")
async def admin_object_update(request:Request):
   query_param=dict(request.query_params)
   table,is_serialize=query_param.get("table",None),int(query_param.get("is_serialize",1))
   if not table:return error("query param table missing")
   body_json=await request.json()
   if body_json.get("parent_table") and body_json.get("parent_table") not in list(table_id.values()):return error("wrong parent_table")
   body_json["updated_by_id"]=request.state.user["id"]
   response=await postgres_update(table,[body_json],is_serialize,postgres_client,postgres_column_datatype,object_serialize)
   if response["status"]==0:return error(response["message"])
   output=response["message"]
   return {"status":1,"message":output}

@app.delete("/my/delete-ids-soft")
async def my_delete_ids_soft(request:Request):
   body_json=await request.json()
   table,ids=body_json.get("table",None),body_json.get("ids",None)
   if not table or not ids:return error("body json table/ids missing")
   if table in ["users"]:return error("table not allowed")
   await postgres_client.execute(query=f"update {table} set is_deleted=1 where id in ({ids}) and created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
   return {"status":1,"message":"done"}

@app.delete("/my/delete-ids-hard")
async def my_delete_ids_hard(request:Request):
   body_json=await request.json()
   table,ids=body_json.get("table",None),body_json.get("ids",None)
   if not table or not ids:return error("body json table/ids missing")
   if table in ["users"]:return error("table not allowed")
   if len(ids.split(","))>max_ids_length_delete:return error("ids length not allowed")
   await postgres_client.execute(query=f"delete from {table} where id in ({ids}) and created_by_id=:created_by_id;",values={"created_by_id":request.state.user["id"]})
   return {"status":1,"message":"done"}

@app.delete("/admin/delete-ids-soft")
async def admin_delete_ids_soft(request:Request):
   body_json=await request.json()
   table,ids=body_json.get("table",None),body_json.get("ids",None)
   if not table or not ids:return error("body json table/ids missing")
   if table in ["users"]:return error("table not allowed")
   await postgres_client.execute(query=f"update {table} set is_deleted=1 where id in ({ids});",values={})
   return {"status":1,"message":"done"}

@app.delete("/admin/delete-ids-hard")
async def admin_delete_ids_hard(request:Request):
   body_json=await request.json()
   table,ids=body_json.get("table",None),body_json.get("ids",None)
   if not table or not ids:return error("body json table/ids missing")
   if table in ["users"]:return error("table not allowed")
   if len(ids.split(","))>max_ids_length_delete:return error("ids length not allowed")
   await postgres_client.execute(query=f"delete from {table} where id in ({ids});",values={})
   return {"status":1,"message":"done"}

@app.delete("/my/object-delete")
async def my_object_delete(request:Request):
   query_param=dict(request.query_params)
   table=query_param.get("table",None)
   if not table:return error("query param table missing")
   if "action_" not in table:return error("table not allowed")
   query_param["created_by_id"]=f"=,{request.state.user['id']}"
   response=await create_where_string(postgres_column_datatype,object_serialize,query_param)
   if response["status"]==0:return error(response["message"])
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"delete from {table} {where_string};"
   await postgres_client.fetch_all(query=query,values=where_value)
   return {"status":1,"message":"done"}

@app.get("/public/info")
async def public_info(request:Request):
   globals_dict=globals()
   output={
   "user_api_access":user_api_access,
   "project_data":project_data,
   "postgres_schema":postgres_schema,
   "api_list":[route.path for route in request.app.routes],
   "api_list_root":[route.path for route in request.app.routes if "root/" in route.path],
   "api_list_auth":[route.path for route in request.app.routes if "auth/" in route.path],
   "api_list_my":[route.path for route in request.app.routes if "my/" in route.path],
   "api_list_public":[route.path for route in request.app.routes if "public/" in route.path],
   "api_list_private":[route.path for route in request.app.routes if "private/" in route.path],
   "api_list_admin":[route.path for route in request.app.routes if "admin/" in route.path],
   "redis":await redis_client.info(),
   "table_id":table_id,
   "variable_size_kb":dict(sorted({f"{name} ({type(var).__name__})":sys.getsizeof(var) / 1024 for name, var in globals_dict.items() if not name.startswith("__")}.items(), key=lambda item: item[1], reverse=True))
   }
   return {"status":1,"message":output}

@app.get("/public/redis-get-object")
async def public_redis_get_object(request:Request):
   query_param=dict(request.query_params)
   key=query_param.get("key",None)
   if not key:return error("query param key missing")
   output=await redis_client.get(key)
   if output:output=json.loads(output)
   return {"status":1,"message":output}

@app.post("/public/otp-send-sns")
async def public_otp_send_sns(request:Request):
   body_json=await request.json()
   mobile,entity_id,sender_id,template_id,message=body_json.get("mobile",None),body_json.get("entity_id",None),body_json.get("sender_id",None),body_json.get("template_id",None),body_json.get("message",None)
   if not mobile:return error("body json mobile missing")
   otp=random.randint(100000,999999)
   await postgres_client.execute(query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;",values={"otp":otp,"mobile":mobile})
   if not entity_id:output=sns_client.publish(PhoneNumber=mobile,Message=str(otp))
   else:output=sns_client.publish(PhoneNumber=mobile,Message=message.replace("{otp}",str(otp)),MessageAttributes={"AWS.MM.SMS.EntityId":{"DataType":"String","StringValue":entity_id},"AWS.MM.SMS.TemplateId":{"DataType":"String","StringValue":template_id},"AWS.SNS.SMS.SenderID":{"DataType":"String","StringValue":sender_id},"AWS.SNS.SMS.SMSType":{"DataType":"String","StringValue":"Transactional"}})
   return {"status":1,"message":output}

@app.post("/public/otp-send-ses")
async def public_otp_send_ses(request:Request):
   body_json=await request.json()
   email,sender=body_json.get("email",None),body_json.get("sender",None)
   if not email or not sender:return error("body json email/sender missing")
   otp=random.randint(100000,999999)
   await postgres_client.fetch_all(query="insert into otp (otp,email) values (:otp,:email) returning *;",values={"otp":otp,"email":email})
   to,title,body=[email],"otp from atom",str(otp)
   ses_client.send_email(Source=sender,Destination={"ToAddresses":to},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":body}}})
   return {"status":1,"message":"done"}

@app.post("/private/file-upload-s3")
async def private_file_upload_s3(request:Request):
   body_form_key,body_form_file=await read_body_form(request)
   bucket,key=body_form_key.get("bucket",None),body_form_key.get("key",None)
   if not bucket or not key:return error("body form bucket/key missing")
   key_list=None if key=="uuid" else key.split("---")
   response=await s3_file_upload(s3_client,s3_region_name,bucket,key_list,body_form_file)
   if response["status"]==0:return error(response["message"])
   return response

@app.post("/private/file-upload-s3-presigned")
async def private_file_upload_s3_presigned(request:Request):
   body_json=await request.json()
   bucket,key=body_json.get("bucket",None),body_json.get("key",None)
   if not bucket or not key:return error("body json bucket/key missing")
   if "." not in key:return error("extension must")
   expiry_sec,size_kb=1000,100
   output=s3_client.generate_presigned_post(Bucket=bucket,Key=key,ExpiresIn=expiry_sec,Conditions=[['content-length-range',1,size_kb*1024]])
   for k,v in output["fields"].items():output[k]=v
   del output["fields"]
   output["url_final"]=f"https://{bucket}.s3.{s3_region_name}.amazonaws.com/{key}"
   return {"status":1,"message":output}

@app.post("/admin/db-runner")
async def admin_db_runner(request:Request):
   body_json=await request.json()
   query=body_json.get("query",None)
   if not query:return error("body json query missing")
   output=[]
   stop_word=["drop","delete","update","insert","alter","truncate","create", "rename","replace","merge","grant","revoke","execute","call","comment","set","disable","enable","lock","unlock"]
   for item in stop_word:
       if item in query.lower():return error(f"{item} not allowed in query")
   output=await postgres_client.fetch_all(query=query,values={})
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