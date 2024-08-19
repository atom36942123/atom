#router
from fastapi import APIRouter
router=APIRouter(tags=["database"])

#query runner
from fastapi import Request
@router.get("/{x}/database/qrunner")
async def function_database_qrunner(request:Request,query:str):
   #inherit
   postgres_object=request.state.postgres_object
   #logic
   query=query
   values={}
   output=await postgres_object.fetch_all(query=query,values=values)
   #final
   return output

#database clean
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/clean")
async def function_database_clean(request:Request):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #creator null
   for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await postgres_object.fetch_all(query=query,values=values)
   #parent null
   for table in ["likes","bookmark","report","block","rating","comment","message"]:
      for parent_table in ["users","post","comment"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         values={}
         output=await postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

#database init
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/init")
async def function_database_init(request:Request):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #extension
   config_database_extension=[
   "create extension if not exists postgis;",
   ]
   for item in config_database_extension:
      query=item
      values={}
      await postgres_object.fetch_all(query=query,values=values)
   #constraint name list
   query="select constraint_name from information_schema.constraint_column_usage;"
   values={}
   output=await postgres_object.fetch_all(query=query,values=values)
   constraint_name_list=[item["constraint_name"] for item in output]
   #table
   config_database_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp"]
   for table in config_database_table:
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      await postgres_object.fetch_all(query=query,values=values)
   #column
   config_database_column={
   "created_at":["timestamptz",config_database_table],
   "created_by_id":["bigint",config_database_table],
   "updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
   "updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
   "is_active":["int",["users","post"]],
   "is_verified":["int",["users","post"]],
   "is_protected":["int",["users","post","box","atom"]],
   "parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
   "parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
   "type":["text",["users","post","box","atom","helpdesk"]],
   "status":["text",["report","helpdesk","message"]],
   "remark":["text",["report","helpdesk"]],
   "rating":["numeric",["rating","atom"]],
   "metadata":["jsonb",["users","post","box","atom"]],
   "username":["text",["users"]],
   "password":["text",["users"]],
   "google_id":["text",["users"]],
   "profile_pic_url":["text",["users"]],
   "last_active_at":["timestamptz",["users"]],
   "name":["text",["users"]],
   "email":["text",["users","post","box","atom","otp"]],
   "mobile":["text",["users","post","box","atom","otp"]],
   "date_of_birth":["date",["users"]],
   "title":["text",["users","post","box","atom"]],
   "description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
   "file_url":["text",["post","box","atom"]],
   "link_url":["text",["post","box","atom"]],
   "tag":["text",["users","post","box","atom"]],
   "otp":["int",["otp"]],
   "tag_array":["text[]",["atom"]],
   "location":["geography(POINT)",["users","post","box","atom"]],
   }
   for k,v in config_database_column.items():
      for table in v[1]:
         query=f"alter table {table} add column if not exists {k} {v[0]};"
         values={}
         await postgres_object.fetch_all(query=query,values=values)
   #created_at default
   for table in config_database_table:
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      await postgres_object.fetch_all(query=query,values=values)
   #protected rows
   for table in config_database_column["is_protected"][1]:
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      await postgres_object.fetch_all(query=query,values=values)
   #not null
   config_database_column_not_null={
   "parent_table":["likes","bookmark","report","block","rating","comment","message"],
   "parent_id":["likes","bookmark","report","block","rating","comment","message"]
   }
   for k,v in config_database_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         await postgres_object.fetch_all(query=query,values=values)
   #query
   config_database_query=[
   "alter table users add constraint constraint_unique_users unique (username);",
   "alter table likes add constraint constraint_unique_likes unique (created_by_id,parent_table,parent_id);",
   "alter table bookmark add constraint constraint_unique_bookmark unique (created_by_id,parent_table,parent_id);",
   "alter table report add constraint constraint_unique_report unique (created_by_id,parent_table,parent_id);",
   "alter table block add constraint constraint_unique_block unique (created_by_id,parent_table,parent_id);",
   "insert into users (username,password,type,is_protected) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','admin',1) on conflict do nothing;",
   "create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;",
   ]
   for query in config_database_query:
      if "add constraint" in query and query.split()[5] in constraint_name_list:
         continue
      else:
         query=query
         values={}
         await postgres_object.fetch_all(query=query,values=values)
   #index
   config_database_index={
   "type":"btree",
   "is_verified":"btree",
   "is_active":"btree",
   "created_by_id":"btree",
   "status":"btree",
   "parent_table":"btree",
   "parent_id":"btree",
   "email":"btree",
   "password":"btree",
   "created_at":"brin",
   "location":"gist"
   }
   for k,v in config_database_column.items():
      for table in v[1]:
         if k in config_database_index:
            query=f"create index if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
            values={}
            await postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
