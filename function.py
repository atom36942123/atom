#elasticsearch
from config import config_elasticsearch_username,config_elasticsearch_password,config_elasticsearch_cloud_id
from elasticsearch import Elasticsearch
async def function_elasticsearch(mode,table,payload):
  elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
  if mode=="create":
    id,data=payload["id"],payload["data"]
    output=elasticsearch_object.index(index=table,id=id,document=data)
  if mode=="read":
    id=payload["id"]
    response=elasticsearch_object.get(index=table,id=id)
  if mode=="update":
    id,data=payload["id"],payload["data"]
    response=elasticsearch_object.update(index=table,id=id,doc=request_body)
  if mode=="delete":
    id=payload["id"]
    response=elasticsearch_object.delete(index=table,id=id)
  if mode=="refresh_table":
    response=elasticsearch_object.indices.refresh(index=table)
  if mode=="search":
    key,value,limit=payload["key"],payload["value"],payload["limit"]
    response=elasticsearch_object.search(index=table,body={"query":{"match":{key:value}},"size":limit})
  return {"status":1,"message":output}
  
#mongo
from config import config_mongo_server
import motor.motor_asyncio
from bson import ObjectId
async def function_mongo(mode,database,table,payload):
  mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server)
  if mode=="create":
    if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(payload)
      output={"status":1,"message":repr(output.inserted_id)}
  if mode=="read":
    if database=="test" and table=="users":
      id=payload["id"]
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
  if mode=="update":
    if database=="test" and table=="users":
      id,data=payload["id"],payload["data"]
      output=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":data})
      output={"status":1,"message":output.modified_count}
  if mode=="delete":
    if database=="test" and table=="users":
      id=payload["id"]
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
      output={"status":1,"message":output.deleted_count}
  return {"status":1,"message":output}
  
#aws
from config import config_aws_access_key_id,config_aws_secret_access_key
from config import  config_s3_bucket_name,config_s3_region_name
from config import config_ses_sender_email,config_ses_region_name
import boto3,uuid
async def function_aws(mode,payload):
  s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="create_presigned_url":
    filename=payload["filename"]
    key=str(uuid.uuid4())+"-"+filename
    output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=key,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
  if mode=="delete_s3_url":
    url=payload["url"]
    key=url.rsplit("/",1)[1]
    output=s3_resource.Object(config_s3_bucket_name,key).delete()
  if mode=="empty_s3_bucket":
    output=s3_resource.Bucket(config_s3_bucket_name).objects.all().delete()
  if mode=="send_email_ses":
    to,title,description=payload["to"],payload["title"],payload["description"]
    output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
  return {"status":1,"message":output}
  
#object create
from config import config_database_column
import hashlib,json
from datetime import datetime
async def function_object_create(postgres_object,table,object_list):
  column_to_insert_list=[*object_list[0]]
  query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    for k,v in object.items():
      datatype=config_database_column[k][0]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if datatype in ["bigint","int"]:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if datatype in ["timestamptz","date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if "[]" in datatype:query_param_list[index][k]=v.split(",") if v else None
  output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":output}

#object update
from config import config_database_column
import hashlib,json
from datetime import datetime
async def function_object_update(postgres_object,table,object_list):
  column_to_update_list=[*object_list[0]]
  column_to_update_list.remove("id")
  query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
  query_param_list=object_list
  for index,object in enumerate(query_param_list):
    if "updated_by_id" not in object:return {"status":0,"message":"updated_by_id missing"}
    for k,v in object.items():
      datatype=config_database_column[k][0]
      if k in ["password","google_id"]:query_param_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if datatype in ["bigint","int"]:query_param_list[index][k]=int(v) if v else None
      if datatype in ["numeric"]:query_param_list[index][k]=round(float(v),3) if v else None
      if datatype in ["timestamptz","date"]:query_param_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["jsonb"]:query_param_list[index][k]=json.dumps(v) if v else None
      if "[]" in datatype:query_param_list[index][k]=v.split(",") if v else None
  output=await postgres_object.execute_many(query=query,values=query_param_list)
  return {"status":1,"message":output}

#object read
from config import config_database_column
import hashlib
from datetime import datetime
async def function_object_read(postgres_object,table,where_param_raw,order,limit,offset):
  where_param={k:v.split(',',1)[1] for k,v in where_param_raw.items()}
  where_param_operator={k:v.split(',',1)[0] for k,v in where_param_raw.items()}
  key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param.items()]
  key_joined=' and '.join(key_list)
  where_string=f"where {key_joined}" if key_joined else ""
  query=f"select * from {table} {where_string} order by {order} limit {limit} offset {offset};"
  query_param=where_param
  for k,v in query_param.items():
    datatype=config_database_column[k][0]
    if k in ["password","google_id"]:query_param[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
    if datatype in ["bigint","int"]:query_param[k]=int(v) if v else None
    if datatype in ["numeric"]:query_param[k]=round(float(v),3) if v else None
    if datatype in ["timestamptz","date"]:query_param[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
    if "[]" in datatype:query_param[k]=v.split(",") if v else None
  output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#database clean
async def function_database_clean(postgres_object):
  for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
    query=f"delete from {table} where created_by_id not in (select id from users);"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  for table in ["likes","bookmark","report","block","rating","comment","message"]:
    for parent_table in ["users","post","comment"]:
      query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":output}

#database init
from config import config_database_extension,config_database_table,config_database_column,config_database_index
from config import config_database_not_null,config_database_identity,config_database_default,config_database_unique,config_database_query
async def function_database_init(postgres_object):
  #extension
  for item in config_database_extension:
    query=f"create extension if not exists {item};"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #table
  for item in config_database_table:
    query=f"create table if not exists {item} ();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #column
  for k,v in config_database_column.items():
    for table in v[1]:
      query=f"alter table {table} add column if not exists {k} {v[0]};"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
  #index
  for k,v in config_database_column.items():
    if k in config_database_index:
      for table in v[1]:
        query=f"create index concurrently if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #schema constraint
  query="select constraint_name from information_schema.constraint_column_usage;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  schema_constraint_name_list=[item["constraint_name"] for item in output]
  #schema column
  query="select * from information_schema.columns where table_schema='public';"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  schema_column=output
  #schema routine
  if False:
    query="select proname from pg_proc;"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
    schema_routine_name_list=[item["proname"] for item in output]
  #protected
  for item in config_database_column["is_protected"][1]:
    query=f"create or replace rule rule_delete_disable_{item} as on delete to {item} where old.is_protected=1 do instead nothing;"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  #not null
  for k,v in config_database_not_null.items():
    for table in v:
      state=[item["is_nullable"] for item in schema_column if item["table_name"]==table and item["column_name"]==k]
      if state[0]=="YES":
        query=f"alter table {table} alter column {k} set not null;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #identity
  for k,v in config_database_identity.items():
    for table in v:
      state=[item["is_identity"] for item in schema_column if item["table_name"]==table and item["column_name"]==k]
      if state[0]=="NO":
        query=f"alter table {table} alter column {k} add generated always as identity;"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #default
  for k,v in config_database_default.items():
    for table in v[1]:
      state=[item["column_default"] for item in schema_column if item["table_name"]==table and item["column_name"]==k]
      if state[0]==None:
        query=f"alter table {table} alter column {k} set default {v[0]};"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #unique
  for k,v in config_database_unique.items():
    for table in v:
      constraint_name=f"constraint_unique_{table}"
      if constraint_name not in schema_constraint_name_list:
        query=f"alter table {table} add constraint {constraint_name} unique ({k});"
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #query
  for item in config_database_query:
      if ("add constraint" in item and item.split()[5] in schema_constraint_name_list):continue
      else:
        query=item
        query_param={}
        output=await postgres_object.fetch_all(query=query,values=query_param)
  #trigger set updated_at
  for item in config_database_column["updated_at"][1]:
    query=f"CREATE OR REPLACE TRIGGER trigger_set_updated_at_now_{item} BEFORE UPDATE ON {item} FOR EACH ROW EXECUTE PROCEDURE function_set_updated_at_now();"
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}

#update last active at
from fastapi import BackgroundTasks
from datetime import datetime
async def function_background_update_last_active_at(postgres_object,user_id):
  background=BackgroundTasks()
  query="update users set last_active_at=:last_active_at where id=:id;"
  query_param={"last_active_at":datetime.now(),"id":user_id}
  background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
  return {"status":1,"message":"done"}

#log
from fastapi import BackgroundTasks
import json
async def function_background_log(postgres_object,created_by_id,request):
  background=BackgroundTasks()
  path=request.url.path
  param=json.dumps(dict(request.query_params))
  body=json.dumps(dict(await request.body()))
 
  
  
 
  query="insert into log (created_by_id,request_path,request_query_param,request_body) values (:created_by_id,:request_path,:request_query_param,:request_body);"
  query_param={"created_by_id":created_by_id,"request_path":path,"request_query_param":param,"request_body":body}
  background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
  return {"status":1,"message":"done"}

#verify otp
async def function_otp_verify(postgres_object,mode,contact,otp):
  if mode not in ["email","mobile"]:return {"status":0,"message":"wrong mode"}
  if mode=="email":query="select otp from otp where email=:contact order by id desc limit 1;"
  if mode=="mobile":query="select otp from otp where mobile=:contact order by id desc limit 1;"
  query_param={"contact":contact}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if not output:return {"status":0,"message":"otp not found"}
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
  return {"status":1,"message":"done"}
  
#auth check
import jwt,json
from config import config_key_jwt,config_key_root
async def function_auth_check(request,mode,user_type_allowed_list):
  if mode not in ["jwt","root"]:return {"status":0,"message":"wrong mode"}
  authorization_header=request.headers.get("Authorization")
  if not authorization_header:return {"status":0,"message":"authorization header is must"}
  token=request.headers.get("Authorization").split(" ",1)[1]
  user=None
  if mode=="root":
    if token!=config_key_root:return {"status":0,"message":"token root issue"}
  if mode=="jwt":
    payload=jwt.decode(token,config_key_jwt,algorithms="HS256")
    data=payload["data"]
    user=json.loads(data)
    if user_type_allowed_list:
      if user["type"] not in user_type_allowed_list:return {"status":0,"message":"user type not allowed"}
  return {"status":1,"message":user}

#token create
import jwt,json,time
from datetime import datetime,timedelta
from config import config_key_jwt
async def function_token_create(user):
  data={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
  data=json.dumps(data,default=str)
  config_token_expiry_days=10000
  expiry_time=time.mktime((datetime.now()+timedelta(days=config_token_expiry_days)).timetuple())
  payload={"exp":expiry_time,"data":data}
  token=jwt.encode(payload,config_key_jwt)
  return {"status":1,"message":token}

#redis key
from fastapi import Request,Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[repr(sorted(request.query_params.items())),namespace,request.method.lower(),request.url.path]
  param=":".join(param)
  return param

#creator key
async def function_add_creator_key(postgres_object,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[item|{"created_by_username":None} for item in object_list]
  user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
  if user_ids:
    query=f"select * from users where id in ({user_ids});"
    query_param={}
    object_user_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_user_list:
         if x["created_by_id"]==y["id"]:
           x["created_by_username"]=y["username"]
           break
  return {"status":1,"message":object_list}

#action count
async def function_add_action_count(postgres_object,object_list,object_table,action_table):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action_table}_count"
  object_list=[item|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_object.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}
  
#delete index all
async def function_delete_index_all(postgres_object):
  query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
  query_param={}
  output=await postgres_object.fetch_all(query=query,values=query_param)
  if output[0]["output"]:
    query=output[0]["output"]
    query_param={}
    output=await postgres_object.fetch_all(query=query,values=query_param)
  return {"status":1,"message":"done"}
