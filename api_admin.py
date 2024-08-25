#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#database init
from fastapi import Request
from config import postgres_object
from config import config_key_root
from config import config_database_extension,config_database_table,config_database_column,config_database_index,config_database_not_null,config_database_identity,config_database_default,config_database_query
from fastapi.responses import JSONResponse
@router.get("/admin/database-init")
async def function_admin_database_init(request:Request):
   #auth check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #extension
   for item in config_database_extension:
      await postgres_object.fetch_all(query=item,values={})
   #table
   for item in config_database_table:
      query=f"create table if not exists {item} ();"
      await postgres_object.fetch_all(query=query,values={})
   [await postgres_object.fetch_all(query=f"alter table {table} add column if not exists {k} {v[0]};",values={}) for k,v in config_database_column.items() for table in v[1]]
   [await postgres_object.fetch_all(query=f"create index concurrently if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});",values={}) for k,v in config_database_column.items() for table in v[1] if k in config_database_index]
   #alter
   [await postgres_object.fetch_all(query=f"alter table {table} alter column {k} set not null;",values={}) for k,v in config_database_not_null.items() for table in v]
   [await postgres_object.fetch_all(query=f"alter table {table} alter column {k} add generated always as identity;",values={}) for k,v in config_database_identity.items() for table in v]
   [await postgres_object.fetch_all(query=f"alter table {table} alter column {k} set default {v[0]};",values={}) for k,v in config_database_default.items() for table in v[1]]
   for item in config_database_column["is_protected"][1]:await postgres_object.fetch_all(query=f"create or replace rule rule_delete_disable_{item} as on delete to {item} where old.is_protected=1 do instead nothing;",values={})
   #query
   output=await postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})
   schema_constraint_name_list=[item["constraint_name"] for item in output]
   for item in config_database_query:
      if ("add constraint" in item and item.split()[5] in schema_constraint_name_list):continue
      else:await postgres_object.fetch_all(query=item,values={})
   #final
   return {"status":1,"message":"done"}

#qrunner
from fastapi import Request
from config import postgres_object
from config import config_key_root
from fastapi.responses import JSONResponse
@router.get("/admin/qrunner")
async def function_admin_qrunner(request:Request,query:str):
   #auth check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #logic
   query=query
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return output

#update cell
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
from datetime import datetime
from function import function_sanitization_query_param_list
@router.put("/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=({"status":0,"message":"admin issue"}))
   #request body
   request_body=await request.json()
   table=request_body["table"]
   id=request_body["id"]
   column=request_body["column"]
   value=request_body["value"]
   #sanitization query_param
   response=await function_sanitization_query_param_list(postgres_object,"update",[{column:value}])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   value=response["message"][0][column]
   #logic
   query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
   query_param={"value":value,"id":id,"updated_at":datetime.now(),"updated_by_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete bulk
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.delete("/admin/delete-bulk")
async def function_admin_delete_bulk(request:Request,table:str,ids:str):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=({"status":0,"message":"admin issue"}))
   #table check
   if table in ["users"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   #check
   if len(ids)>10000:return JSONResponse(status_code=400,content=({"status":0,"message":"ids length exceeded"}))
   #logic
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#database clean
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.delete("/admin/database-clean")
async def function_admin_database_clean(request:Request):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=({"status":0,"message":"admin issue"}))
   #delete object having creator null
   for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
   #delete object having  parent null
   for table in ["likes","bookmark","report","block","rating","comment","message"]:
      for parent_table in ["users","post","comment"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         query_param={}
         output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"done"}

#feed
from fastapi import Request
from config import postgres_object
from function import function_token_check
from function import function_prepare_where
from function import function_sanitization_query_param_list
from fastapi.responses import JSONResponse
@router.get("/admin/feed")
async def function_admin_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=({"status":0,"message":"admin issue"}))
   #request query param
   request_query_param=dict(request.query_params)
   #prepare where
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_prepare_where(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string=response["message"][0]
   where_param=response["message"][1]
   #query set
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   #sanitization query_param
   response=await function_sanitization_query_param_list(postgres_object,"read",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
