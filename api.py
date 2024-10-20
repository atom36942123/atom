#router
from fastapi import APIRouter
router=APIRouter()

#index
from fastapi import Request
@router.get("/")
async def root(request:Request):
  response={"status":1,"message":"welcome to atom"}
  return response

#root/create-postgres-schema
from pschema import postgres_schema_default
from fastapi import Request
@router.post("/root/create-postgres-schema")
async def root_create_postgres_schema(request:Request,mode:str):
   #start
   postgres_client=request.state.postgres_client
   #assign schema
   if mode=="default":postgres_schema_init=postgres_schema_default
   if mode=="self":postgres_schema_init=await request.json()
   #create extension
   for item in postgres_schema_init["extension"]:
      query=f"create extension if not exists {item}"
      await postgres_client.fetch_all(query=query,values={})
   #create table
   postgres_schema_table=await postgres_client.fetch_all(query="select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE';",values={})
   postgres_schema_table_name_list=[item["table_name"] for item in postgres_schema_table]
   for item in postgres_schema_init["table"]:
      if item not in postgres_schema_table_name_list:
         query=f"create table if not exists {item} (id bigint primary key generated always as identity not null);"
         await postgres_client.fetch_all(query=query,values={})
   #create column
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_column_table={f"{item['column_name']}_{item['table_name']}":item["data_type"] for item in postgres_schema_column}
   for k,v in postgres_schema_init["column"].items():
      for item in v[1]:
         if f"{k}_{item}" not in postgres_schema_column_table:
            query=f"alter table {item} add column if not exists {k} {v[0]};"
            await postgres_client.fetch_all(query=query,values={})
   #alter notnull
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   postgres_schema_column_table_nullable={f"{item['column_name']}_{item['table_name']}":item["is_nullable"] for item in postgres_schema_column}
   for k,v in postgres_schema_init["not_null"].items():
      for item in v:
         if postgres_schema_column_table_nullable[f"{k}_{item}"]=="YES":
            query=f"alter table {item} alter column {k} set not null;"
            await postgres_client.fetch_all(query=query,values={})
   #alter unique
   postgres_schema_constraint=await postgres_client.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
   postgres_schema_constraint_name_list=[item["constraint_name"] for item in postgres_schema_constraint]
   for k,v in postgres_schema_init["unique"].items():
      for item in v:
         constraint_name=f"constraint_unique_{k}_{item}".replace(',','_')
         if constraint_name not in postgres_schema_constraint_name_list:
            query=f"alter table {item} add constraint {constraint_name} unique ({k});"
            await postgres_client.fetch_all(query=query,values={})
   #create index
   postgres_schema_index=await postgres_client.fetch_all(query="select indexname from pg_indexes where schemaname='public';",values={})
   postgres_schema_index_name_list=[item["indexname"] for item in postgres_schema_index]
   for k,v in postgres_schema_init["index"].items():
      for item in v[1]:
         index_name=f"index_{k}_{item}"
         if index_name not in postgres_schema_index_name_list:
            query=f"create index concurrently if not exists {index_name} on {item} using {v[0]} ({k});"
            await postgres_client.fetch_all(query=query,values={})
   #delete disable bulk
   await postgres_client.fetch_all(query="create or replace function function_delete_disable_bulk() returns trigger language plpgsql as $$declare n bigint := tg_argv[0]; begin if (select count(*) from deleted_rows) <= n is not true then raise exception 'cant delete more than % rows', n; end if; return old; end;$$;",values={})
   for k,v in postgres_schema_init["bulk_delete_disable"].items():
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
   for k,v in postgres_schema_init["query"].items():
      if "add constraint" in v and v.split()[5] in postgres_schema_constraint_name_list:continue
      await postgres_client.fetch_all(query=v,values={})
   #final
   return {"status":1,"message":"done"}

#root/postgres-query-runner
from fastapi import Request
@router.get("/root/postgres-query-runner")
async def root_postgres_query_runner(request:Request,query:str):
   #start
   postgres_client=request.state.postgres_client
   #query run
   for item in query.split("---"):output=await postgres_client.fetch_all(query=item,values={})
   #final
   return {"status":1,"message":output}

#root/grant all api access
from fastapi import Request
@router.put("/root/grant-all-api-access")
async def root_grant_all_api_access(request:Request,user_id:int):
   #start
   postgres_client=request.state.postgres_client
   app=request.state.app
   #set api admin list
   api_admin_list=[route.path for route in router.routes if "/admin" in route.path]
   api_admin_str=",".join(api_admin_list)
   #update api access
   query="update users set api_access=:api_access where id=:id returning *"
   query_param={"api_access":api_admin_str,"id":user_id}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#auth/signup
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def auth_signup(request:Request,username:str,password:str):
   #start
   postgres_client=request.state.postgres_client
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":{"user":user,"token":response["message"]}}

#auth/login
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
@router.get("/auth/login")
async def auth_login(request:Request,username:str,password:str,mode:str=None):
   #start
   postgres_client=request.state.postgres_client
   #read user
   query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #check user
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if mode=="admin" and not user["api_access"]:return JSONResponse(status_code=400,content={"status":0,"message":"no admin"})
   #token create
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#auth/login-google
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
@router.get("/auth/login-google")
async def auth_login_google(request:Request,google_id:str):
   #start
   postgres_client=request.state.postgres_client
   #read user
   query=f"select * from users where google_id=:google_id order by id desc limit 1;"
   query_param={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   #create user
   if not user:
     query=f"insert into users (google_id) values (:google_id) returning *;"
     query_param={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user=output[0]
   #token create
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#auth/login-email-otp
from config import secret_key_jwt
from function import create_token
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
@router.get("/auth/login-email-otp")
async def auth_login_email_otp(request:Request,email:str,otp:int,mode:str=None):
   #start
   postgres_client=request.state.postgres_client
   #verify otp
   response=await verify_otp("email",postgres_client,otp,email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user
   query=f"select * from users where email=:email order by id desc limit 1;"
   query_param={"email":email}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if mode=="exist" and not user:return JSONResponse(status_code=400,content={"status":1,"message":"no user"})
   #create user
   if not user:
     query=f"insert into users (email) values (:email) returning *;"
     query_param={"email":email}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user=output[0]
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#auth/login-mobile-otp
from config import secret_key_jwt
from function import create_token
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from datetime import datetime,timezone
@router.get("/auth/login-mobile-otp")
async def auth_login_mobile_otp(request:Request,mobile:str,otp:int,mode:str=None):
   #start
   postgres_client=request.state.postgres_client
   #verify otp
   response=await verify_otp("mobile",postgres_client,otp,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #read user
   query=f"select * from users where mobile=:mobile order by id desc limit 1;"
   query_param={"mobile":mobile}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if mode=="exist" and not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #create user
   if not user:
     query=f"insert into users (mobile) values (:mobile) returning *;"
     query_param={"mobile":mobile}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user_id=output[0]["id"]
     query="select * from users where id=:id;"
     query_param={"id":user_id}
     output=await postgres_client.fetch_all(query=query,values=query_param)
     user=output[0]
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#auth/login-email-password
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
@router.get("/auth/login-email-password")
async def auth_login_email_password(request:Request,email:str,password:str):
   #start
   postgres_client=request.state.postgres_client
   #read user
   query=f"select * from users where email=:email and password=:password order by id desc limit 1;"
   query_param={"email":email,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#auth/login-mobile-password
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
@router.get("/auth/login-mobile-password")
async def auth_login_mobile_password(request:Request,mobile:str,password:str):
   #start
   postgres_client=request.state.postgres_client
   #read user
   query=f"select * from users where mobile=:mobile and password=:password order by id desc limit 1;"
   query_param={"mobile":mobile,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/profile
from function import update_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
@router.get("/my/profile")
async def my_profile(request:Request):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response={"status":1,"message":user}
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   await update_postgres_object(postgres_client,postgres_schema_column_data_type,"background","users",[object])
   #final
   return response

#my/token-refresh
from config import secret_key_jwt
from function import create_token
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/token-refresh")
async def my_token_refresh(request:Request):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #read user
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   #create token
   response=await create_token(secret_key_jwt,user)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
   
#my/delete-account
from fastapi import Request
from fastapi.responses import JSONResponse
@router.delete("/my/delete-account")
async def my_delete_account(request:Request):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #check
   if user["is_protected"]==1:return JSONResponse(status_code=400,content={"status":0,"message":"not allowed"})
   #delete user
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"account deleted"}

#my/message-received
from function import update_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/my/message-received")
async def my_message_received(request:Request,background:BackgroundTasks,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #read message
   query=f"select * from message where user_id=:user_id order by {order} limit {limit} offset {(page-1)*limit};"
   if mode=="unread":query=f"select * from message where user_id=:user_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #mark status read
   if output:
      object_list=[{"id":item["id"],"status":"read","updated_by_id":user["id"]} for item in output]
      await update_postgres_object(postgres_client,postgres_schema_column_data_type,"background","message",object_list)
   #final
   return {"status":1,"message":output}

#my/message-inbox
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/message-inbox")
async def my_message_inbox(request:Request,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #read inbox
   query=f"with mcr as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
   if mode=="unread":query=f"with mcr as (select id,abs(created_by_id-user_id) as unique_id from message where (created_by_id=:created_by_id or user_id=:user_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where user_id=:user_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"user_id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/message-thread
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/my/message-thread")
async def my_message_thread(request:Request,background:BackgroundTasks,user_id:int,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #read message thread
   query=f"select * from message where ((created_by_id=:user_1 and user_id=:user_2) or (created_by_id=:user_2 and user_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #mark status read
   query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where created_by_id=:created_by_id and user_id=:user_id returning *;"
   query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"user_id":user["id"]}
   background.add_task(await postgres_client.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}

#my/delete-message
from fastapi import Request
from fastapi.responses import JSONResponse
@router.delete("/my/delete-message")
async def my_delete_message(request:Request,mode:str,id:int=None):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #logic
   if mode=="created":
      query="delete from message where created_by_id=:created_by_id;"
      query_param={"created_by_id":user["id"]}
   if mode=="received":
      query="delete from message where user_id=:user_id;"
      query_param={"user_id":user["id"]}
   if mode=="all":
      query="delete from message where (created_by_id=:created_by_id or user_id=:user_id);"
      query_param={"created_by_id":user["id"],"user_id":user["id"]}
   if mode=="single":
      if not id:return JSONResponse(status_code=400,content={"status":0,"message":"id must"})
      query="delete from message where id=:id and (created_by_id=:created_by_id or user_id=:user_id);"
      query_param={"id":id,"created_by_id":user["id"],"user_id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/parent-read
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/parent-read")
async def my_parent_read(request:Request,table:str,parent_table:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #read parent ids
   query=f"select parent_id from {table} where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null) order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   parent_ids_list=[item["parent_id"] for item in output]
   #read parent ids data
   query=f"select * from {parent_table} join unnest(array{parent_ids_list}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
   output=await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":output}

#my/parent-check
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/parent-check")
async def my_parent_check(request:Request,table:str,parent_table:str,parent_ids:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #read parent ids to check
   parent_ids_input=[int(item) for item in parent_ids.split(",")]
   query=f"select parent_id from {table} join unnest(array{parent_ids_input}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and (created_by_id=:created_by_id or :created_by_id is null);"
   query_param={"parent_table":parent_table,"created_by_id":user["id"]}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   parent_ids_output=[item["parent_id"] for item in output if item["parent_id"]]
   #create mapping
   mapping={item:1 if item in parent_ids_output else 0 for item in parent_ids_input}
   #final
   return {"status":1,"message":mapping}

#my/update-email
from function import update_postgres_object
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime,timezone
@router.put("/my/update-email")
async def my_update_email(request:Request,email:str,otp:int):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #verify otp
   response=await verify_otp("email",postgres_client,otp,email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #update email
   object={"id":user["id"],"email":email,"updated_by_id":user["id"]}
   response=await update_postgres_object(postgres_client,postgres_schema_column_data_type,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/update-mobile
from function import update_postgres_object
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime,timezone
@router.put("/my/update-mobile")
async def my_update_mobile(request:Request,mobile:str,otp:int):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #verify otp
   response=await verify_otp("mobile",postgres_client,otp,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #update mobile
   object={"id":user["id"],"mobile":mobile,"updated_by_id":user["id"]}
   response=await update_postgres_object(postgres_client,postgres_schema_column_data_type,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/delete-ids
from fastapi import Request
from fastapi.responses import JSONResponse
@router.delete("/my/delete-ids")
async def my_delete_ids(request:Request,table:str,ids:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   #check      
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids.split(","))>3:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   #delete ids
   query=f"delete from {table} where created_by_id=:created_by_id and id in ({ids});"
   query_param={"created_by_id":user["id"]}
   await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"done"}

#my/object create
from function import create_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
@router.post("/my/object-create")
async def my_object_create(request:Request,table:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #check table
   if table not in ["post","likes","bookmark","report","block","rating","comment","message","helpdesk"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #object set
   object=await request.json()
   object["created_by_id"]=user["id"]
   #object check
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   #object create
   response=await create_postgres_object(postgres_client,postgres_schema_column_data_type,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/object-read
from function import read_where_clause
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/object-read")
async def my_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #read where clause
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #read object
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#my/object-update
from function import update_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
@router.put("/my/object-update")
async def my_object_update(request:Request,table:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   object=await request.json()
   object["updated_by_id"]=user["id"]
   #check table
   if table in ["spatial_ref_sys","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #check keys allowed
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   if table=="users":
      for item in ["email","mobile"]:
         if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   #check ownership
   if table=="users" and object["id"]!=user["id"]:return JSONResponse(status_code=400,content={"status":0,"message":"ownership issue"})
   if table!="users":
      query=f"select * from {table} where id=:id;"
      query_param={"id":object["id"]}
      output=await postgres_client.fetch_all(query=query,values=query_param)
      object=output[0] if output else None
      if not object:return JSONResponse(status_code=400,content={"status":0,"message":"no object"})
      if object["created_by_id"]!=user["id"]:return JSONResponse(status_code=400,content={"status":0,"message":"ownership issue"})
   #logic
   response=await update_postgres_object(postgres_client,postgres_schema_column_data_type,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#my/object-delete
from function import read_where_clause
from fastapi import Request
from fastapi.responses import JSONResponse
@router.delete("/my/object-delete")
async def my_object_delete(request:Request,table:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #check
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #read where clause
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #delete object
   query=f"delete from {table} {where_string};"
   query_param=where_value
   await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"done"}

#my/search-location
from function import read_where_clause
from function import search_postgres_location
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/my/search-location")
async def my_location_search(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #read where clause
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #logic
   response=await search_postgres_location(postgres_client,table,location,within,order,limit,(page-1)*limit,where_string,where_value)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public/api-list
from fastapi import Request
@router.get("/public/api-list")
async def public_api_list(request:Request,mode:str=None):
   #start
   app=request.state.app
   #logic
   api_list=[route.path for route in app.routes]
   if mode=="admin":api_list=[route.path for route in app.routes if "/admin" in route.path]
   #final
   return {"status":1,"message":api_list}

#public/table-column
from fastapi import Request
@router.get("/public/table-column")
async def public_table_column(request:Request,table:str=None):
   #start
   postgres_client=request.state.postgres_client
   #logic
   postgres_schema_column=await postgres_client.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   table_list=list(set([item['table_name'] for item in postgres_schema_column]))
   temp={}
   for item in table_list:temp[item]={column["column_name"]:column["data_type"] for column in postgres_schema_column if column['table_name']==item}
   if table:temp=temp[table]
   #final
   return {"status":1,"message":temp}

#public/project meta
from function import read_redis_key
from fastapi_cache.decorator import cache
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/public/project-meta")
@cache(expire=60,key_builder=read_redis_key)
async def public_project_meta(request:Request):
   #start
   postgres_client=request.state.postgres_client
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   temp={k:await postgres_client.fetch_all(query=v,values={}) for k,v in query_dict.items()}
   response={"status":1,"message":temp}
   #final
   return response

#public/otp send mobile sns
from config import sns_region_name,sns_access_key_id,sns_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3,random
@router.get("/public/otp-send-mobile-sns")
async def public_otp_send_mobile_sns(request:Request,mobile:str):
   #start
   postgres_client=request.state.postgres_client
   #send otp
   otp=random.randint(100000,999999)
   sns_client=boto3.client("sns",region_name=sns_region_name,aws_access_key_id=sns_access_key_id,aws_secret_access_key=sns_secret_access_key)
   output=sns_client.publish(PhoneNumber=mobile,Message=f"otp={otp}")
   #save otp
   query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;"
   query_param={"otp":otp,"mobile":mobile}
   await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#public/otp send email ses
from config import ses_region_name,ses_access_key_id,ses_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3,random
@router.get("/public/otp-send-email-ses")
async def public_otp_send_email_ses(request:Request,identity:str,email:str):
   #start
   postgres_client=request.state.postgres_client
   #send otp
   otp=random.randint(100000,999999)
   ses_client=boto3.client("ses",region_name=ses_region_name,aws_access_key_id=ses_access_key_id,aws_secret_access_key=ses_secret_access_key)
   output=ses_client.send_email(Source=identity,Destination={"ToAddresses":[email]},Message={"Subject":{"Charset":"UTF-8","Data":"otp"},"Body":{"Text":{"Charset":"UTF-8","Data":str(otp)}}})
   #save otp
   query="insert into otp (otp,email) values (:otp,:email) returning *;"
   query_param={"otp":otp,"email":email}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"otp sent"}

#public/otp verify email
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/public/otp-verify-email")
async def public_otp_verify_email(request:Request,otp:int,email:str):
   #start
   postgres_client=request.state.postgres_client
   #logic
   response=await verify_otp("email",postgres_client,otp,email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public/otp verify mobile
from function import verify_otp
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/public/otp-verify-mobile")
async def public_otp_verify_mobile(request:Request,otp:int,mobile:str):
   #start
   postgres_client=request.state.postgres_client
   #logic
   response=await verify_otp("mobile",postgres_client,otp,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public/object read
from function import read_where_clause
from function import read_redis_key
from function import add_creator_key
from function import add_action_count
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
@router.get("/public/object-read")
@cache(expire=60,key_builder=read_redis_key)
async def public_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #check table
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #read where clause
   param=dict(request.query_params)
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #read object
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #add creator key
   response=await add_creator_key(postgres_client,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #add likes count
   response=await add_action_count(postgres_client,"likes",table,response["message"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #add bookmark count
   response=await add_action_count(postgres_client,"bookmark",table,response["message"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#private/object read
from function import read_where_clause
from function import read_redis_key
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
@router.get("/private/object-read")
@cache(expire=60,key_builder=read_redis_key)
async def private_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #check table
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #read where clause
   param=dict(request.query_params)
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #read object
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#private/s3 upload file
from config import s3_access_key_id,s3_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import UploadFile
import boto3,uuid
@router.post("/private/s3-upload-file")
async def private_s3_upload_file(request:Request,s3_region_name:str,s3_bucket_name:str,file:UploadFile):
   #logic
   key=str(uuid.uuid4())+"-"+file.filename
   s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   s3_client.upload_fileobj(file.file,s3_bucket_name,key)
   s3_url=f"https://{s3_bucket_name}.s3.amazonaws.com/{key}"
   #final
   return {"status":1,"message":s3_url}

#private/s3 create presigned url
from config import s3_access_key_id,s3_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3,uuid
@router.get("/private/s3-create-presigned-url")
async def private_s3_create_presigned_url(request:Request,s3_region_name:str,s3_bucket_name:str,filename:str):
   #logic
   if "." not in filename:return JSONResponse(status_code=400,content={"status":0,"message":"extension must"})
   key=str(uuid.uuid4())+"-"+filename
   s3_client=boto3.client("s3",region_name=s3_region_name,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=s3_bucket_name,Key=key,ExpiresIn=60,Conditions=[['content-length-range',1,250*1024]])
   output["s3_url"]=f"https://{s3_bucket_name}.s3.amazonaws.com/{key}"
   #final
   return {"status":1,"message":output}

#private/rekognition compare face
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.get("/private/rekognition-compare-face")
async def private_rekognition_compare_face(request:Request,s3_url_source:str,s3_url_target:str):
   #logic
   bucket_name_source=s3_url_source.split("//",1)[1].split(".",1)[0]
   bucket_name_target=s3_url_target.split("//",1)[1].split(".",1)[0]
   key_source=s3_url_source.rsplit("/",1)[1]
   key_target=s3_url_target.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.compare_faces(SourceImage={"S3Object":{"Bucket":bucket_name_source,"Name":key_source}},TargetImage={"S3Object":{"Bucket":bucket_name_target,"Name":key_target}},SimilarityThreshold=80)
   #final
   return {"status":1,"message":output}

#private/rekognition detetct label
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.get("/private/rekognition-detect-label")
async def private_rekognition_detect_label(request:Request,s3_url:str):
   #logic
   bucket_name=s3_url.split("//",1)[1].split(".",1)[0]
   key=s3_url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MaxLabels=10,MinConfidence=90)
   #final
   return {"status":1,"message":output}

#private/rekognition detetct face
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.get("/private/rekognition-detect-face")
async def private_rekognition_detect_face(request:Request,s3_url:str):
   #logic
   bucket_name=s3_url.split("//",1)[1].split(".",1)[0]
   key=s3_url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_faces(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},Attributes=['ALL'])
   #final
   return {"status":1,"message":output}

#private/rekognition detect moderation
from config import rekognition_region_name,rekognition_access_key_id,rekognition_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.get("/private/rekognition-detect-moderation")
async def private_rekognition_detect_moderation(request:Request,s3_url:str):
   #logic
   bucket_name=s3_url.split("//",1)[1].split(".",1)[0]
   key=s3_url.rsplit("/",1)[1]
   rekognition_client=boto3.client("rekognition",region_name=rekognition_region_name,aws_access_key_id=rekognition_access_key_id,aws_secret_access_key=rekognition_secret_access_key)
   output=rekognition_client.detect_moderation_labels(Image={"S3Object":{"Bucket":bucket_name,"Name":key}},MinConfidence=80)
   #final
   return {"status":1,"message":output}

#private/openai
from config import secret_key_openai
from fastapi import Request
from fastapi.responses import JSONResponse
from langchain_community.llms import OpenAI
@router.get("/private/openai")
async def private_openai(request:Request,text:str):
   #logic
   llm=OpenAI(api_key=secret_key_openai,temperature=0.7)
   output=llm(text)
   #final
   return {"status":1,"message":output}

#admin/update-api-access
from fastapi import Request
from pydantic import BaseModel
class schema_update_api_access(BaseModel):
   user_id:int
   api_access:str|None=None
@router.put("/admin/update-api-access")
async def admin_update_api_access(request:Request,body:schema_update_api_access):
   #middleware
   postgres_client=request.state.postgres_client
   app=request.state.app
   #check api access string
   api_admin_list=[route.path for route in app.routes if "/admin" in route.path]
   api_admin_str=",".join(api_admin_list)
   if body.api_access:
      for item in body.api_access.split(","):
         if item not in api_admin_str:return JSONResponse(status_code=400,content={"status":0,"message":"wrong api access string"})
   #update api access
   query="update users set api_access=:api_access where id=:id returning *"
   query_param={"id":body.user_id,"api_access":body.api_access}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#admin/postgres clean
from fastapi import Request
from fastapi.responses import JSONResponse
@router.delete("/admin/postgres-clean")
async def admin_pclean(request:Request):
   #start
   postgres_client=request.state.postgres_client
   #delete creator null data
   for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      await postgres_client.fetch_all(query=query,values={})
   #delete parent null data
   for table in ["likes","bookmark","report","block","rating","comment","message"]:
      for parent_table in ["users","post","comment"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":"done"}

#admin/csv
from function import create_postgres_object
from function import update_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import UploadFile
import csv,codecs
@router.post("/admin/csv-uploader")
async def admin_csv_uploader(request:Request,mode:str,table:str,file:UploadFile):
   #start
   postgres_client=request.state.postgres_client
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #set object list
   if file.content_type!="text/csv":return {"status":0,"message":"file extension must be csv"}
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   object_list=[]
   for row in file_csv:object_list.append(row)
   await file.close()
   #logic
   if mode=="create":response=await create_postgres_object(postgres_client,postgres_schema_column_data_type,"background",table,object_list)
   if mode=="update":response=await update_postgres_object(postgres_client,postgres_schema_column_data_type,"background",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin/s3 delete url
from config import s3_access_key_id,s3_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.delete("/admin/s3-delete-url")
async def admin_s3_delete_url(request:Request,s3_url:str):
   #logic
   bucket_name=s3_url.split("//",1)[1].split(".",1)[0]
   key=s3_url.rsplit("/",1)[1]
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Object(bucket_name,key).delete()
   #final
   return {"status":1,"message":output}

#admin/s3 empty bucket
from config import s3_access_key_id,s3_secret_access_key
from fastapi import Request
from fastapi.responses import JSONResponse
import boto3
@router.delete("/admin/s3-empty-bucket")
async def admin_s3_empty_bucket(request:Request,bucket_name:str):
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Bucket(bucket_name).objects.all().delete()
   #final
   return {"status":1,"message":output}

#admin/delete ids
from fastapi import Request
from fastapi.responses import JSONResponse
@router.put("/admin/delete-ids")
async def admin_delete_ids(request:Request,table:str,ids:str):
   #start
   postgres_client=request.state.postgres_client
   #logic
   query=f"delete from {table} where id in ({ids});"
   await postgres_client.fetch_all(query=query,values={})
   #final
   return {"status":1,"message":"done"}

#admin/postgres-query-runner
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/admin/postgres-query-runner")
async def admin_postgres_query_runner(request:Request,query:str):
  #start
  postgres_client=request.state.postgres_client
  #query check
  for item in ["insert","update","delete","alter","drop"]:
    if item in query:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed in query"})
  #query run
  output=await postgres_client.fetch_all(query=query,values={})
  #final
  return {"status":1,"message":output}

#admin/object-read
from function import read_where_clause
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/admin/object-read")
async def admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #start
   postgres_client=request.state.postgres_client
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #read where clause
   param=dict(request.query_params)
   response=await read_where_clause(postgres_schema_column_data_type,param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   #read object
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   output=await postgres_client.fetch_all(query=query,values=where_value)
   response={"status":1,"message":output}
   #final
   return response

#admin/object-update
from function import update_postgres_object
from fastapi import Request
from fastapi.responses import JSONResponse
@router.put("/admin/object-update")
async def admin_object_update(request:Request,table:str):
   #start
   postgres_client=request.state.postgres_client
   user=request.state.user
   postgres_schema_column_data_type=request.state.postgres_schema_column_data_type
   #check table
   if table in ["spatial_ref_sys","otp","log"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #object set
   object=await request.json()
   object["updated_by_id"]=user["id"]
   #object update
   response=await update_postgres_object(postgres_client,postgres_schema_column_data_type,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

