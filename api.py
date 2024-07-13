#import
from config import *
from query import *
from schema import *
from function import *
from object import postgres_object
from fastapi import Request,Depends
from fastapi_limiter.depends import RateLimiter
import hashlib

#router
from fastapi import APIRouter
router=APIRouter(tags=["api","xxx"])

#root
@router.get("/")
async def function_api_root():
   return {"status":1,"message":"welcome to atom"}

#database
@router.get("/{x}/database-create")
async def function_api_database_create(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #table create
    for item in config_table:
        query=f"create table if not exists {item} (id bigint primary key generated always as identity);"
        response=await function_query_runner(postgres_object[x],"write",query,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column create
    for k,v in config_column.items():
        for table in v[1]:
            query=f"alter table {table} add column if not exists {k} {v[0]};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #final response
    return {"status":1,"message":"database create done"}

@router.get("/{x}/database-alter")
async def function_api_database_alter(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #read schema column
    response=await function_query_runner(postgres_object[x],"read",query_schema_column,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_column=response["message"]
    #read schema constraint
    response=await function_query_runner(postgres_object[x],"read",query_schema_constraint,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #default
    for column in schema_column:
        for k,v in config_column_default.items():
            for table in v[1]:
                if column["table_name"]==table and column["column_name"]==k and not column["column_default"]:
                    query=f"alter table {table} alter column {k} set default {v[0]};"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #checkin
    for k,v in config_column_checkin.items():
        for table in v[1]:
            constraint_name=f"checkin_{k}_{table}"
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #not nullable
    for column in schema_column:
        for k,v in config_column_not_nullable.items():
            for table in v:
                if column["table_name"]==table and column["column_name"]==k and column["is_nullable"]=="YES":
                    query=f"alter table {table} alter column {k} set not null;"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #unique
    for k,v in config_column_unique.items():
        for table in v:
            constraint_name=f"unique_{k.replace(',','_')}_{table}".replace(",","_")
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")    
    #final response
    return {"status":1,"message":"database alter done"}

@router.get("/{x}/database-index")
async def function_api_database_index(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #drop all index
    response=await function_drop_all_index(postgres_object[x],function_query_runner)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #create index
    for k,v in config_column_index.items():
        for table in v[1]:
            index_name=f"index_{k.replace(',','_')}_{table}"
            query=f"create index if not exists {index_name} on {table}({k});"
            if v[0]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"database index done"}

@router.get("/{x}/database-query")
async def function_api_database_query(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #logic
    for item in [query_create_root_user,query_rule_delete_disable_users_root]:
        response=await function_query_runner(postgres_object[x],"write",item,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #finally
    return {"status":1,"message":"database query done"}

#signup
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_api_signup(x:str,request:Request,body:schema_signup):
   #param validaton
   response=await function_param_validation(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #read user
   query="select * from users where username=:username;"
   values={"username":body.username}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #check username if exist
   if response["message"]:return function_http_response(400,0,"username already exist")
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.post("/{x}/login")
async def function_api_login(x:str,request:Request,body:schema_login):
   #param validation
   response=await function_param_validation(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #username
   if body.mode=="username":
      #check body must
      if not body.username or not body.password:return function_http_response(400,0,"username/password must")
      #read user
      query="select * from users where username=:username and password=:password;"
      values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check user if not exist
      if not response["message"]:return function_http_response(400,0,"no such user")
      #user define
      user=response["message"][0]
   #firebase
   if body.mode=="firebase":
      #check body must
      if not body.firebase:return function_http_response(400,0,"firebase_id must")
      #read user
      query="select * from users where firebase_id=:firebase_id order by id desc limit 1;"
      values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (firebase_id) values (:firebase_id) returning *;"
         values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #email
   if body.mode=="email":
      #check body must
      if not body.email or not body.otp:return function_http_response(400,0,"email is must")
      #read otp
      query="select * from otp where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check if otp exist
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      #verify otp
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (email) values (:email) returning *;"
         values={"email":body.email}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #mobile
   if body.mode=="mobile":
      #check body must
      if not body.mobile or not body.otp:return function_http_response(400,0,"mobile is must")
      #read otp
      query="select * from otp where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check if otp exist
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      #verify otp
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body.mobile}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/token-refresh")
async def function_api_token_refresh(x:str,request:Request):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #read user
   query="select * from users where id=:id;"
   values={"id":request_user["id"]}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #if user not exist
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   #user define
   user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response


