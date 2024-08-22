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
