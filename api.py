from function import *

#import


from fastapi import BackgroundTasks

from fastapi_cache.decorator import cache
import random,codecs,jwt,time,boto3,uuid
from datetime import timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch






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
   #body={"username":"xxx","password":"123"}
   if "mode" not in body:
      query="select * from users where username=:username and password=:password order by id desc limit 1;"
      values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #body={"mode":"google","google_id":"123"}
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
   #body={"mode":"email","email":"xxx","otp":123}
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
   #body={"mode":"mobile","mobile":"xxx","otp":123}
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
   #body={"mode":"token_refresh"}
   if "mode" in body and body["mode"]=="token_refresh":
      user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
      if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
      query="select * from users where id=:id;"
      values={"id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #token encode
   user={"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   user_extra={"x":str(request.url.path).split("/")[1],"created_at_token":datetime.today().strftime('%Y-%m-%d')}
   data=json.dumps(user|user_extra,default=str)
   expiry_time=time.mktime((datetime.now()+timedelta(days=100000)).timetuple())
   payload={"exp":expiry_time,"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}

@router.get("/{x}/profile")
async def function_profile(request:Request,background:BackgroundTasks):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #user object
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=dict(output[0]) if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #user extra info
   user_extra_info={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "message_unread_count":"select count(*) from message where parent_table='users' and parent_id=:user_id and status is null;"
   }
   temp={}
   for k,v in user_extra_info.items():
      query=v
      values={"user_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #background
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":user|temp}

#body={"table":"post","type":"xxx","description":"xxx"}
#body={"table":"likes","parent_table":"post","parent_id":1}
@router.post("/{x}/create")
async def function_create(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] in ["users","atom","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set
   column_to_insert_list=[item for item in [*body] if item not in ["table"]+["id","created_at","is_active","is_verified","google_id","otp"]]+["created_by_id"]
   query=f"insert into {body['table']} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
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

#body={"table":"users","id":1,"name":"neo","gender":"male"}
@router.post("/{x}/update")
async def function_update(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #query set
   column_to_update_list=[item for item in [*body] if item not in ["table","id"]+["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
   query=f"update {body['table']} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   #values
   values={}
   for item in column_to_update_list:
      if item in body:values[item]=body[item]
      else:values[item]=None
   values["updated_at"]=datetime.now()
   values["updated_by_id"]=user["id"]
   values["id"]=user["id"] if body['table']=="users" else body["id"]
   values["created_by_id"]=None if body['table']=="users" else user["id"]
   if "metadata" in values:values["metadata"]=json.dumps(values["metadata"],default=str)
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/read")
async def function_read(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #read object
   body["created_by_id"]=user["id"]
   response=await function_read_object(request.state.postgres_object,body)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}

@router.post("/{x}/delete")
async def function_delete(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #logic
   #body={"mode":"object","table":"post","id":123}
   if body["mode"]=="object":
      query=f"delete from {body['table']} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
      values={}
      values["id"]=user["id"] if body['table']=="users" else body["id"]
      values["created_by_id"]=None if body['table']=="users" else user["id"]
   #body={"mode":"message_all"}
   if body["mode"]=="message_all":
      query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
      values={"created_by_id":user['id'],"parent_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

@router.post("/{x}/my")
async def function_my(request:Request,background:BackgroundTasks):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
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
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {offset}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
      values={"created_by_id":user["id"],"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_inbox_unread"}
   if body["mode"]=="message_inbox_unread":
      query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {offset};"
      values={"created_by_id":user["id"],"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_received"}
   if body["mode"]=="message_received":
      query=f"select * from message where parent_table='users' and parent_id=:parent_id order by {order} limit {limit} offset {offset};"
      values={"parent_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"message_thread","user_id":2}
   if body["mode"]=="message_thread":
      query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {offset};"
      values={"user_1":user["id"],"user_2":body["user_id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      query="update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      values={"status":"read","created_by_id":body["user_id"],"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #body={"mode":"parent_read","table":"likes","parent_table":"post"}
   if body["mode"]=="parent_read":
      query=f"select parent_id from {body['table']} where parent_table=:parent_table and created_by_id=:created_by_id order by {order} limit {limit} offset {offset};"
      values={"parent_table":body["parent_table"],"created_by_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      parent_ids=[item["parent_id"] for item in output]
      query=f"select * from {body['parent_table']} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #body={"mode":"parent_check","table":"likes","parent_table":"post","parent_ids":[1,2,3]}
   if body["mode"]=="parent_check":
      query=f"select parent_id from {body['table']} join unnest(array{body['parent_ids']}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
      values={"parent_table":body["parent_table"],"created_by_id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      output=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #final
   return {"status":1,"message":output}

@router.post("/{x}/admin")
async def function_admin(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
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
   if body['table'] not in ["users","post","atom"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #read object
   response=await function_read_object(request.state.postgres_object,body)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add action count
   response=await function_add_action_count(request.state.postgres_object,output,body["table"],"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
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
      if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
      output=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).Object(config_s3_bucket_name,body["url"].rsplit("/",1)[1]).delete()
   #body={"mode":"s3_delete_bucket_key_all"}
   if body["mode"]=="s3_delete_bucket_key_all":
      if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
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

