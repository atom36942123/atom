#router
from fastapi import APIRouter
router = APIRouter()

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
   database=request.state.postgres_object.fetch_all
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #config
   config_database={
   "created_at":["timestamptz","users,post,action,activity,box,atom"],
   "created_by_id":["bigint","users,post,action,activity,box,atom"],
   "updated_at":["timestamptz","users,post,action,activity,box,atom"],
   "updated_by_id":["bigint","users,post,action,activity,box,atom"],
   "is_active":["int","users,post,action,activity,box,atom"],
   "is_verified":["int","users,post,action,activity,box,atom"],
   "is_protected":["int","users,post,action,activity,box,atom"],
   "type":["text","users,post,action,activity,box,atom"],
   "status":["text","users,post,action,activity,box,atom"],
   "remark":["text","users,post,action,activity,box,atom"],
   "metadata":["jsonb","users,post,action,activity,box,atom"],
   "parent_table":["text","action,activity"],
   "parent_id":["bigint","action,activity"],
   "last_active_at":["timestamptz","users"],
   "google_id":["text","users"],
   "otp":["int","box"],
   "username":["text","users"],
   "password":["text","users"],
   "name":["text","users"],
   "email":["text","users,post,box,atom"],
   "mobile":["text","users,post,box,atom"],
   "title":["text","users,post,box,atom"],
   "description":["text","users,post,action,activity,box,atom"],
   "tag":["text","users,post,box,atom"],
   "link":["text","users,post,box,atom"],
   "file":["text","users,post,box,atom"],
   "rating":["numeric","users,post,box,atom"],
   }
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
   #created_at default
   for table in config_database["created_at"][1].split(','):
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #protected rows
   for table in config_database["is_protected"][1].split(','):
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #set not null
   config_column_not_null={"created_by_id":["action","activity"],"parent_table":["action","activity"],"parent_id":["action","activity"]}
   for k,v in config_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #schema constraint
   query="select constraint_name from information_schema.constraint_column_usage;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   schema_constraint_name_list=[item["constraint_name"] for item in output]
   #query zzz
   config_query_zzz=["alter table users add constraint constraint_unique_users unique (username);",
   "alter table action add constraint constraint_unique_action unique (type,created_by_id,parent_table,parent_id);"
   ]
   for item in config_query_zzz:
      if item.split()[5] not in schema_constraint_name_list:
         query=item
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #drop index
   query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if output[0]["output"]:
      query=output[0]["output"]
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #schema column
   query="select * from information_schema.columns where table_schema='public' order by column_name;"
   values={}
   schema_column=await request.state.postgres_object.fetch_all(query=query,values=values)
   #create index
   mapping_index_datatype={"text":"btree","bigint":"btree","integer":"btree","numeric":"btree","timestamp with time zone":"brin","date":"brin","jsonb":"gin","ARRAY":"gin"}
   config_column_index=["type","is_verified","is_active","created_by_id","status","parent_table","parent_id","email","password","created_at"]
   for column in schema_column:
      if column['column_name'] in config_column_index:
         query=f"create index if not exists index_{column['column_name']}_{column['table_name']} on {column['table_name']} using {mapping_index_datatype[column['data_type']]} ({column['column_name']});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
   
@router.post("/{x}/csv")
async def function_csv(request:Request,file:UploadFile):
   #prework
   database=request.state.postgres_object.fetch_all
   database_bulk=request.state.postgres_object.execute_many
   if request.headers.get("token")!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #schema column groupby
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
   #file
   filename=file.filename.split(".")[0]
   table=filename.rsplit("_",1)[0]
   mode=filename.rsplit("_",1)[1]
   #file csv
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_csv_column_list=file_csv.fieldnames
   #values
   values=[]
   for row in file_csv:
      for column in file_csv_column_list:
         if column not in schema_column_datatype:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"column not in the schema"}))
         if column in ["password","google_id"]:row[column]=hashlib.sha256(row[column].encode()).hexdigest() if row[column] else None  
         if schema_column_datatype[column] in ["jsonb"]:row[column]=json.dumps(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["ARRAY"]:row[column]=row[column].split(",") if row[column] else None
         if schema_column_datatype[column] in ["integer","bigint"]:row[column]=int(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["decimal","numeric","real","double precision"]:row[column]=round(float(row[column]),3) if row[column] else None
         if schema_column_datatype[column] in ["date","timestamp with time zone"]:row[column]=datetime.strptime(row[column],'%Y-%m-%d') if row[column] else None
      values.append(row)
   await file.close()
   #query set
   if mode=="create":
      column_1=','.join(file_csv_column_list)
      column_2=','.join([':'+item for item in file_csv_column_list])
      query=f"insert into {table} ({column_1}) values ({column_2}) returning *;"
      values=values
   if mode=="update":
      param=[item for item in file_csv_column_list if item not in ["id"]]
      column=""
      for k in param:column=column+f"{k}=coalesce(:{k},{k}),"
      column=column[:-1]
      query=f"update {table} set {column} where id=:id returning *;"
      values=values
   if mode=="delete":
      query=f"delete from {table} where id=:id;"
      values=values
   #query run
   output=await database_bulk(query=query,values=values)
   #final
   return {"status":1,"message":f"{table}_{mode}={len(values)}"}

@router.get("/{x}/clean")
async def function_clean(request:Request):
   #prewrok
   database=request.state.postgres_object.fetch_all
   #config
   config_clean_table_creator=["post","action","activity"]
   config_clean_table_parent=["action","activity"]
   #created_by_id null
   for table in config_clean_table_creator:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #parent_id null
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
   #prewrok
   database=request.state.postgres_object.fetch_all
   temp={}
   query_dict={"user_count":"select count(*) from users;"}
   #logic
   for k,v in query_dict.items():
      query=v
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])
@router.get("/{x}/feed")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_feed(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   body=dict(request.query_params)
   #config
   config_table_allowed_feed=["users","post","atom"]
   if body['table'] not in config_table_allowed_feed:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #schema column groupby
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
   #body preprocessing
   for k,v in body.items():
      if k in schema_column_datatype:
         if schema_column_datatype[k] in ["ARRAY"]:body[k]=v.split(",")
         if schema_column_datatype[k] in ["integer","bigint"]:body[k]=int(v)
         if schema_column_datatype[k] in ["decimal","numeric","real","double precision"]:body[k]=float(v)
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
   output=[dict(item) for item in output]
   #add creator key
   object_list=output
   object_table=table
   if object_list and object_table in ["post"]:
      object_list=[item|{"created_by_username":None} for item in object_list]
      user_ids=','.join([str(item["created_by_id"]) for item in object_list if item["created_by_id"]])
      if user_ids:
         query=f"select * from users where id in ({user_ids});"
         values={}
         object_user_list=await request.state.postgres_object.fetch_all(query=query,values=values)
         for object in object_list:
            for object_user in object_user_list:
               if object["created_by_id"]==object_user["id"]:
                  object["created_by_username"]=object_user["username"]
                  break
   #add action count
   object_list=object_list
   object_table=table
   action_type="comment"
   action_table="activity"
   key_name=f"{action_type}_count"
   if object_list and object_table in ["post"]:
      object_list=[item|{key_name:0} for item in object_list]
      parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
      if parent_ids:
         query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where type=:type and parent_table=:parent_table group by parent_id;"
         values={"type":action_type,"parent_table":object_table}
         object_action_list=await request.state.postgres_object.fetch_all(query=query,values=values)
         for object in object_list:
            for object_action in object_action_list:
               if object["id"]==object_action["parent_id"]:
                  object[key_name]=object_action["count"]
                  break
   #final
   return {"status":1,"message":object_list}
   
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_signup(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   body=await request.json()
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/login")
async def function_login(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
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
      query="select otp from box where type='otp' and email=:email order by id desc limit 1;"
      values={"email":body["email"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
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
      query="select otp from box where type='otp' and mobile=:mobile order by id desc limit 1;"
      values={"mobile":body["mobile"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
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
   expiry_days=1
   data=json.dumps({"x":str(request.url).split("/")[3],"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple()),"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}
   
@router.get("/{x}/profile")
async def function_profile(request:Request,background:BackgroundTasks):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   user=dict(user)
   #count key
   query_dict={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "comment_count":"select count(*) from activity where type='comment' and created_by_id=:user_id;",
   "message_unread_count":"select count(*) from activity where type='message' and parent_table='users' and parent_id=:user_id and status is null;"
   }
   for k,v in query_dict.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user[k]=output[0]["count"]
   #background task
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":user}

@router.post("/{x}/create")
async def function_create(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #config
   config_table_allowed_create=["post","action","activity","box"]
   if body['table'] not in config_table_allowed_create:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body preprocessing
   body["created_by_id"]=user["id"]
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   #query set
   table=body["table"]
   column_1=None
   column_2=None
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
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
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

