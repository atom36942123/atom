#router
from fastapi import APIRouter
router=APIRouter()

#helper
from helper import *

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   return {"status":1,"message":await request.state.postgres_object.fetch_all(query=query,values={})}

@router.post("/{x}/insert-csv")
async def function_insert_csv(request:Request,table:str,file:UploadFile):
   #check
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"only csv allowed"}))
   if file.size>=100000:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file size should be<=100000 bytes"}))
   #logic
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   if set(file_object.fieldnames)!=set(["created_by_id","type","title","description","file_url","link_url","tag"]):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"csv column mismatch-ct2t"}))
   values=[]
   for row in file_object:
      row["created_by_id"]=int(row["created_by_id"]) if row["created_by_id"] else None
      row["tag"]=row["tag"].split(",") if row["tag"] else None
      values.append(row)
   file.file.close   
   return {"status":1,"message":await request.state.postgres_object.execute_many(query=f"insert into {table} (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;",values=values)}

@router.get("/{x}/metric")
async def function_metric(request:Request):
   return {"status":1,"message":{"config_database_length":len(config_database)}}

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
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
   return {"status":1,"message":"done"}

@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   body=await request.json()
   if not body["username"] or not body["password"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"body issue"}))
   return {"status":1,"message":await request.state.postgres_object.fetch_all(query="insert into users (username,password) values (:username,:password) returning *;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})}
 
@router.post("/{x}/login")
async def function_login(x:str,request:Request):
   body=await request.json()
   if len(body)>2:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"body issue"}))
   #otp verify
   if "otp" in body:
      output=await request.state.postgres_object.fetch_all(query="select * from otp where (email=:email or :email is null) and (mobile=:mobile or :mobile is null) order by id desc limit 1;",values={"email":body["email"],"mobile":body["mobile"]})
      if not output:return function_http_response(400,0,"otp not exist")
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
   #values
   body["username"]=body["username"] if "username" in body else None
   body["password"]=hashlib.sha256(body["password"].encode()).hexdigest() if "password" in body else None
   body["email"]=body["email"] if "email" in body else None
   body["mobile"]=body["mobile"] if "mobile" in body else None
   body["firebase_id"]=hashlib.sha256(body["firebase_id"].encode()).hexdigest() if "firebase_id" in body else None
   body["google_id"]=hashlib.sha256(body["google_id"].encode()).hexdigest() if "google_id" in body else None
   #read user
   output=await request.state.postgres_object.fetch_all(query="select * from users where (username=:username or :username is null) and (password=:password or :password is null) and (email=:email or :email is null) and (mobile=:mobile or :mobile is null) and (firebase_id=:firebase_id or :firebase_id is null) and (google_id=:google_id or :google_id is null) order by id desc limit 1;",values=body)
   user=output[0] if output else None
   #create user
   if not user:
      if "username" in body:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
      output=await request.state.postgres_object.fetch_all(query="insert into users (firebase_id,google_id,email,mobile) values (:firebase_id,:google_id,:email,:mobile) returning *;",values={k:v for k,v in body.items() if k not in ["username","password"]})
      user=await request.state.postgres_object.fetch_all(query="select * from users where id=:id;",values={"id":output[0]["id"]})[0]
   #final response
   return {"status":1,"message":jwt.encode(json.dumps({"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)|{"exp":time.mktime((datetime.now()+timedelta(days=int(36500))).timetuple())},env("key"))}



                   

    


   
   
