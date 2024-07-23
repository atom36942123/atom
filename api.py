#router
from fastapi import APIRouter
router=APIRouter()

#helper
from helper import *

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   return {"status":1,"message":output}

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

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   #prework
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
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


   
   
