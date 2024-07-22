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
9
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   body=await request.json()
   if not body["username"] or not body["password"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"body issue"}))
   return {"status":1,"message":await request.state.postgres_object.fetch_all(query="insert into users (username,password) values (:username,:password) returning *;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})}
   


      

      
# @router.post("/{x}/login")
# async def function_login(x:str,request:Request):
#    body=await request.json()
#    #opt verify
#    await request.state.postgres_object.fetch_all(query=query,values={})}
   
#    if response:
#        if response["status"]==0:return function_http_response(400,0,response["message"])
#        if not response["message"]:return function_http_response(400,0,"otp not exist")
#        if response["message"][0]["otp"]!=body["otp"]:return function_http_response(400,0,"otp mismatched")
#    #read user
#    if all(item in body for item in ["username","password"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where username=:username and password=:password;",{"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})
#    if all(item in body for item in ["firebase_id"]):respomse=await function_query_runner(request.state.postgres_object,"read","select * from users where firebase_id=:firebase_id order by id desc limit 1;",{"firebase_id":hashlib.sha256(body["firebase_id"].encode()).hexdigest()})
#    if all(item in body for item in ["email","otp"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where email=:email order by id desc limit 1;",{"email":body["email"]})
#    if all(item in body for item in ["mobile","otp"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where mobile=:mobile order by id desc limit 1;",{"mobile":body["mobile"]})
#    if response["status"]==0:return function_http_response(400,0,response["message"])
#    user=None if not response["message"] else response["message"][0]
#    #not user
#    if all(item in body for item in ["username","password"]) and not user:return function_http_response(400,0,"no such user")
#    if all(item in body for item in ["firebase_id"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (firebase_id) values (:firebase_id) returning *;",{"firebase_id":hashlib.sha256(body["firebase_id"].encode()).hexdigest()})
#    if all(item in body for item in ["email","otp"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (email) values (:email) returning *;",{"email":body["email"]})
#    if all(item in body for item in ["mobile","otp"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (mobile) values (:mobile) returning *;",{"mobile":body["mobile"]})
#    if response["status"]==0:return function_http_response(400,0,response["message"])
#    #read user
#    if not user:
#        response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":response["message"]})
#        if response["status"]==0:return function_http_response(400,0,response["message"])
#        user=response["message"][0]
#    #token encode
#    data=json.dumps({"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
#    response=await function_token_encode(data,env("key"))
#    if response["status"]==0:return function_http_response(400,0,response["message"])
#    #final response
#    return response




    
    
    
    
     




                   

    


   
   
