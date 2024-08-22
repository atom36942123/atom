#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#update cell
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from function import function_sanitization_query_param_list
@router.put("/{x}/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check jwt
   response=await function_token_check_jwt(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   #request body
   request_body=await request.json()
   table=request_body["table"]
   id=request_body["id"]
   column=request_body["column"]
   value=request_body["value"]
   #sanitization query_param
   response=await function_sanitization_query_param_list(postgres_object,"update",[{column:value}])
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   value=response["message"][0][column]
   #logic
   query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
   query_param={"value":value,"id":id,"updated_at":datetime.now(),"updated_by_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete bulk
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/admin/delete-bulk")
async def function_admin_delete_bulk(request:Request,table:str,ids:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check jwt
   response=await function_token_check_jwt(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   #table check
   if table in ["users"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #logic
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#database clean
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/clean")
async def function_database_clean(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check root
   response=await function_token_check_root(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
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
