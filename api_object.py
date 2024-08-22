#router
from fastapi import APIRouter
router=APIRouter(tags=["object"])

#create
from fastapi import Request
from function import function_token_check
from function import function_sanitization_query_param_list
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/object/create")
async def function_object_create(request:Request,table:str):
   #postgres object 
   postgres_object=request.state.postgres_object
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #table check
   if table in ["users","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #request body
   request_body=await request.json()
   #column_to_insert_list
   column_to_insert_list=[*request_body]+["created_by_id"]
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in column_to_insert_list:column_to_insert_list.remove(item)
   #query set
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   #query_param set
   query_param={}
   for item in column_to_insert_list:
      if item in request_body:query_param[item]=request_body[item]
   query_param["created_by_id"]=user["id"]
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"create",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#update
from fastapi import Request
from datetime import datetime
from function import function_token_check
from function import function_sanitization_query_param_list
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.put("/{x}/object/update")
async def function_object_update(request:Request,table:str,id:int):
   #postgres object  
   postgres_object=request.state.postgres_object
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #request body
   request_body=await request.json()
   #column_to_update_list
   column_to_update_list=[*request_body]+["updated_at","updated_by_id"]
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in column_to_update_list:column_to_update_list.remove(item)
   #query set
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   #query_param set
   query_param={}
   for item in column_to_update_list:
      if item in request_body:query_param[item]=request_body[item]
   query_param["updated_at"]=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
   query_param["updated_by_id"]=user["id"]
   query_param["id"]=id
   query_param["created_by_id"]=user["id"]
   if table=="users":query_param["id"],query_param["created_by_id"]=user["id"],None
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"update",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete
from fastapi import Request
from function import function_token_check
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/object/delete")
async def function_object_delete(request:Request,table:str,id:int):
   #postgres object  
   postgres_object=request.state.postgres_object
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #delete object
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   query_param={"id":id,"created_by_id":user["id"]}
   if table=="users":query_param["id"],query_param["created_by_id"]=user["id"],None
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#read
from fastapi import Request
from function import function_token_check
from function import function_sanitization_query_param_list
from function import function_prepare_where
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/object/read")
async def function_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #postgres object  
   postgres_object=request.state.postgres_object
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   user=response["message"]
   #request query param
   request_query_param=dict(request.query_params)
   #prepare where
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   where_param_raw["created_by_id"]=f"=,{user['id']}"
   response=await function_prepare_where(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   where_string=response["message"][0]
   where_param=response["message"][1]
   #query set
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"read",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
