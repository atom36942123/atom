#openai
from langchain_community.llms import OpenAI
async def openai_prompt(secret_key_openai,text):
   llm=OpenAI(api_key=secret_key_openai,temperature=0.7)
   output=llm(text)
   return {"status":1,"message":output}
   
#rekognition detect moderation
import boto3
async def rekognition_detect_moderation(aws_access_key_id,aws_secret_access_key,rekognition_region_name,bucket_name,key):
   client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.detect_moderation_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MinConfidence=80)
   return {"status":1,"message":output}

#rekognition detect label
import boto3
async def rekognition_detect_face(aws_access_key_id,aws_secret_access_key,rekognition_region_name,bucket_name,key):
   client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.detect_faces(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},Attributes=['ALL'])
   return {"status":1,"message":output}

#rekognition detect label
import boto3
async def rekognition_detect_label(aws_access_key_id,aws_secret_access_key,rekognition_region_name,bucket_name,key):
   client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.detect_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MaxLabels=10,MinConfidence=90)
   return {"status":1,"message":output}

#rekognition compare face
import boto3
async def rekognition_compare_face(aws_access_key_id,aws_secret_access_key,rekognition_region_name,bucket_name_1,key_1,bucket_name_2,key_2):
   client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.compare_faces(SourceImage={"S3Object":{"Bucket":bucket_name_1,"Name":key_1}},TargetImage={"S3Object":{"Bucket":bucket_name_2,"Name":key_2}},SimilarityThreshold=80)
   return {"status":1,"message":output}

#s3 empty bucket
import boto3
async def s3_empty_bucket(aws_access_key_id,aws_secret_access_key,bucket_name):
   resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=resource.Bucket(bucket_name).objects.all().delete()
   return {"status":1,"message":output}

#s3 delete url
import boto3
async def s3_delete_key(aws_access_key_id,aws_secret_access_key,bucket_name,key):
   resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=resource.Object(bucket_name,key).delete()
   return {"status":1,"message":output}
   
#s3 create presigned url
import boto3
async def s3_create_presigned_url(aws_access_key_id,aws_secret_access_key,s3_region_name,bucket_name,key,expiry_sec,size_kb):
   s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=bucket_name,Key=key,ExpiresIn=expiry_sec,Conditions=[['content-length-range',1,size_kb*1024]])
   return {"status":1,"message":output}

#s3 upload file
import boto3
async def s3_upload_file(aws_access_key_id,aws_secret_access_key,s3_region_name,bucket_name,key,file):
   client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.upload_fileobj(file,bucket_name,key)
   return {"status":1,"message":output}

#ses send email
import boto3
async def ses_send_email(aws_access_key_id,aws_secret_access_key,ses_region_name,sender,to_list,title,body):
   client=boto3.client("ses",region_name=ses_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.send_email(Source=sender,Destination={"ToAddresses":to_list},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":body}}})
   return {"status":1,"message":output}

#sns send message
import boto3
async def sns_send_message(aws_access_key_id,aws_secret_access_key,sns_region_name,mobile,message):
   client=boto3.client("sns",region_name=sns_region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   output=client.publish(PhoneNumber=mobile,Message=message)
   return {"status":1,"message":output}

#mongo create object
#call=await mongo_create_object(mongo_client,"atom","users",[{"_id":1,"username":"atom"},{"_id":2,"username":"neo"}])
async def mongo_create_object(mongo_client,database,table,object_list):
   db=mongo_client[database]
   collection=db[table]
   output=await collection.insert_many(object_list)
   return {"status":1,"message":output}

#mongo read object
#call=await mongo_read_object(mongo_client,"atom","users",1)
async def mongo_read_object(mongo_client,database,table,id):
   db=mongo_client[database]
   collection=db[table]
   output=await collection.find_one({"_id":id})
   return {"status":1,"message":output}

#mongo update object
#call=await mongo_update_object(mongo_client,"atom","users",1,{"username":"atom2"})
async def mongo_update_object(mongo_client,database,table,id,object):
   db=mongo_client[database]
   collection=db[table]
   output=await collection.update_one({"_id":id},{"$set":object})
   return {"status":1,"message":output}

#mongo delete object
#call=await mongo_delete_object(mongo_client,"atom","users",1)
async def mongo_delete_object(mongo_client,database,table,id):
   db=mongo_client[database]
   collection=db[table]
   output=await collection.delete_one({"_id":id})
   return {"status":1,"message":output}
 
#redis set object
import json
async def redis_set_object(redis_client,key_list,object_list):
   for index,object in enumerate(object_list):
      key=str(key_list[index])
      object=json.dumps(object)
      async with redis_client.pipeline(transaction=True) as pipe:output=await (pipe.set(key,object)).execute()
   return {"status":1,"message":output}

#redis get object 
async def redis_get_object(redis_client,key):
   async with redis_client.pipeline(transaction=True) as pipe:
      output=await pipe.get(key).execute()
      if output!=[None]:output=json.loads(output[0])
   return {"status":1,"message":output}

#read redis key
from fastapi import Request,Response
def read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
   param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
   param=":".join(param)
   return param

#verify otp
from datetime import datetime,timezone
async def verify_otp(mode,postgres_client,otp,contact):
   if mode=="email":query="select * from otp where email=:contact order by id desc limit 1;"
   if mode=="mobile":query="select * from otp where mobile=:contact order by id desc limit 1;"
   query_param={"contact":contact}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   if not output:return {"status":0,"message":"otp not found"}
   if int(datetime.now(timezone.utc).strftime('%s'))-int(output[0]["created_at"].strftime('%s'))>60:return {"status":0,"message":"otp expired"}
   if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
   return {"status":1,"message":"done"}

#create token
import jwt,json,time
from datetime import datetime,timedelta
async def create_token(secret_key_jwt,user):
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"],"is_protected":user["is_protected"]}
   expiry_time=time.mktime((datetime.now()+timedelta(days=100000000)).timetuple())
   payload={"exp":expiry_time,"data":json.dumps(user,default=str)}
   token=jwt.encode(payload,secret_key_jwt)
   return {"status":1,"message":token}

#add creator key
async def add_creator_key(postgres_client,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[dict(item)|{"created_by_username":None} for item in object_list]
  user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
  if user_ids:
    query=f"select * from users where id in ({user_ids});"
    query_param={}
    object_user_list=await postgres_client.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_user_list:
         if x["created_by_id"]==y["id"]:
           x["created_by_username"]=y["username"]
           break
  return {"status":1,"message":object_list}

#add action count
async def add_action_count(postgres_client,action,object_table,object_list):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action}_count"
  object_list=[dict(item)|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_client.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}

#read where clause
import hashlib
from datetime import datetime
async def read_where_clause(postgres_schema_column_data_type,param):
   param={k:v for k,v in param.items() if k not in ["table","order","limit","page"]}
   param={k:v for k,v in param.items() if k not in ["location","metadata"]}
   param={k:v for k,v in param.items() if k in postgres_schema_column_data_type}
   where_key_value={k:v.split(',',1)[1] for k,v in param.items()}
   where_key_operator={k:v.split(',',1)[0] for k,v in param.items()}
   key_list=[f"({k} {where_key_operator[k]} :{k} or :{k} is null)" for k,v in where_key_value.items()]
   key_joined=' and '.join(key_list)
   where_string=f"where {key_joined}" if key_joined else ""
   for k,v in where_key_value.items():
      if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
      else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
      if k in ["password","google_id"]:where_key_value[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:where_key_value[k]=int(v) if v else None
      if datatype in ["numeric"]:where_key_value[k]=round(float(v),3) if v else None
      if "time" in datatype:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["ARRAY"]:where_key_value[k]=v.split(",") if v else None
   return {"status":1,"message":[where_string,where_key_value]}

#search postgres location 
async def search_postgres_location(postgres_client,table,location,within,order,limit,offset,where_string,where_value):
  long,lat=float(location.split(",")[0]),float(location.split(",")[1])
  min_meter,max_meter=int(within.split(",")[0]),int(within.split(",")[1])
  query=f'''
  with
  x as (select * from {table} {where_string}),
  y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x)
  select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {offset};
  '''
  output=await postgres_client.fetch_all(query=query,values=where_value)
  return {"status":1,"message":output}

#create postgres object
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def create_postgres_object(postgres_client,postgres_schema_column_data_type,mode,table,object_list):
   if not object_list:return {"status":0,"message":"object list empty"}
   if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
   column_to_insert_list=[*object_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   for index,object in enumerate(object_list):
      for k,v in object.items():
         if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
         else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
         if not v:object_list[index][k]=None
         if k in ["password","google_id"]:object_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if "int" in datatype:object_list[index][k]=int(v) if v else None
         if datatype in ["numeric"]:object_list[index][k]=round(float(v),3) if v else None
         if "time" in datatype:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["date"]:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["jsonb"]:object_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:object_list[index][k]=v.split(",") if v else None
   background=BackgroundTasks()
   output=f"{len(object_list)} object created"
   if mode=="background":
      if len(object_list)==1:background.add_task(await postgres_client.fetch_all(query=query,values=object_list[0]))
      else:background.add_task(await postgres_client.execute_many(query=query,values=object_list))
   if mode=="normal":
      if len(object_list)==1:output=await postgres_client.fetch_all(query=query,values=object_list[0])
      else:output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

#update postgres object
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def update_postgres_object(postgres_client,postgres_schema_column_data_type,mode,table,object_list):
   if not object_list:return {"status":0,"message":"object list empty"}
   if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
   column_to_update_list=[*object_list[0]]
   column_to_update_list.remove("id")
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   for index,object in enumerate(object_list):
      for k,v in object.items():
         if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
         else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
         if not v:object_list[index][k]=None
         if k in ["password","google_id"]:object_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if "int" in datatype:object_list[index][k]=int(v) if v else None
         if datatype in ["numeric"]:object_list[index][k]=round(float(v),3) if v else None
         if "time" in datatype:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["date"]:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["jsonb"]:object_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:object_list[index][k]=v.split(",") if v else None
   background=BackgroundTasks()
   output=f"{len(object_list)} object updated"
   if mode=="background":
      if len(object_list)==1:background.add_task(await postgres_client.fetch_all(query=query,values=object_list[0]))
      else:background.add_task(await postgres_client.execute_many(query=query,values=object_list))
   else:
      if len(object_list)==1:output=await postgres_client.fetch_all(query=query,values=object_list[0])
      else:output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

#create postgres schema
async def create_postgres_schema(postgres_client,postgres_schema):
   #create extension
   for item in postgres_schema["extension"]:
      query=f"create extension if not exists {item}"
      await postgres_client.fetch_all(query=query,values={})
   #create table
   postgres_schema_table=await postgres_client.fetch_all(query="select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE';",values={})
   postgres_schema_table_name_list=[item["table_name"] for item in postgres_schema_table]
   for item in postgres_schema["table"]:
      if item not in postgres_schema_table_name_list:
         query=f"create table if not exists {item} (id bigint primary key generated always as identity not null);"
         await postgres_client.fetch_all(query=query,values={})
   #create column
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_column_table={f"{item['column_name']}_{item['table_name']}":item["data_type"] for item in postgres_schema_column}
   for k,v in postgres_schema["column"].items():
      for item in v[1]:
         if f"{k}_{item}" not in postgres_schema_column_table:
            query=f"alter table {item} add column if not exists {k} {v[0]};"
            await postgres_client.fetch_all(query=query,values={})
   #alter notnull
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_column_table_nullable={f"{item['column_name']}_{item['table_name']}":item["is_nullable"] for item in postgres_schema_column}
   for k,v in postgres_schema["not_null"].items():
      for item in v:
         if postgres_schema_column_table_nullable[f"{k}_{item}"]=="YES":
            query=f"alter table {item} alter column {k} set not null;"
            await postgres_client.fetch_all(query=query,values={})
   #alter unique
   postgres_schema_constraint=await postgres_client.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
   postgres_schema_constraint_name_list=[item["constraint_name"] for item in postgres_schema_constraint]
   for k,v in postgres_schema["unique"].items():
      for item in v:
         constraint_name=f"constraint_unique_{k}_{item}".replace(',','_')
         if constraint_name not in postgres_schema_constraint_name_list:
            query=f"alter table {item} add constraint {constraint_name} unique ({k});"
            await postgres_client.fetch_all(query=query,values={})
   #create index
   postgres_schema_index=await postgres_client.fetch_all(query="select indexname from pg_indexes where schemaname='public';",values={})
   postgres_schema_index_name_list=[item["indexname"] for item in postgres_schema_index]
   for k,v in postgres_schema["index"].items():
      for item in v[1]:
         index_name=f"index_{k}_{item}"
         if index_name not in postgres_schema_index_name_list:
            query=f"create index concurrently if not exists {index_name} on {item} using {v[0]} ({k});"
            await postgres_client.fetch_all(query=query,values={})
   #delete disable bulk
   await postgres_client.fetch_all(query="create or replace function function_delete_disable_bulk() returns trigger language plpgsql as $$declare n bigint := tg_argv[0]; begin if (select count(*) from deleted_rows) <= n is not true then raise exception 'cant delete more than % rows', n; end if; return old; end;$$;",values={})
   for k,v in postgres_schema["bulk_delete_disable"].items():
      trigger_name=f"trigger_delete_disable_bulk_{k}"
      query=f"create or replace trigger {trigger_name} after delete on {k} referencing old table as deleted_rows for each statement execute procedure function_delete_disable_bulk({v});"
      await postgres_client.fetch_all(query=query,values={})
   #set created_at default (auto)
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   for item in postgres_schema_column:
      if item["column_name"]=="created_at" and not item["column_default"]:
         query=f"alter table only {item['table_name']} alter column created_at set default now();"
         await postgres_client.fetch_all(query=query,values={})
   #set updated at now (auto)
   await postgres_client.fetch_all(query="create or replace function function_set_updated_at_now() returns trigger as $$ begin new.updated_at= now(); return new; end; $$ language 'plpgsql';",values={})
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_trigger=await postgres_client.fetch_all(query="select trigger_name from information_schema.triggers;",values={})
   postgres_schema_trigger_name_list=[item["trigger_name"] for item in postgres_schema_trigger]
   for item in postgres_schema_column:
      if item["column_name"]=="updated_at":
         trigger_name=f"trigger_set_updated_at_now_{item['table_name']}"
         if trigger_name not in postgres_schema_trigger_name_list:
            query=f"create or replace trigger {trigger_name} before update on {item['table_name']} for each row execute procedure function_set_updated_at_now();"
            await postgres_client.fetch_all(query=query,values={})
   #create rule protection (auto)
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_rule=await postgres_client.fetch_all(query="select rulename from pg_rules;",values={})
   postgres_schema_rule_name_list=[item["rulename"] for item in postgres_schema_rule]
   for item in postgres_schema_column:
      if item["column_name"]=="is_protected":
         rule_name=f"rule_delete_disable_{item['table_name']}"
         if rule_name not in postgres_schema_rule_name_list:
            query=f"create or replace rule {rule_name} as on delete to {item['table_name']} where old.is_protected=1 do instead nothing;"
            await postgres_client.fetch_all(query=query,values={})
   #run misc query
   postgres_schema_constraint=await postgres_client.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
   postgres_schema_constraint_name_list=[item["constraint_name"] for item in postgres_schema_constraint]
   for k,v in postgres_schema["query"].items():
      if "add constraint" in v and v.split()[5] in postgres_schema_constraint_name_list:continue
      await postgres_client.fetch_all(query=v,values={})
   return {"status":1,"message":"done"}