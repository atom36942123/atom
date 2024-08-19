#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#import for raising error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import for auth check jwt
from config import config_key_jwt
import jwt
import json

#update cell
from fastapi import Request
from datetime import datetime
from function import function_sanitization_query_param_list
@router.put("/{x}/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #database 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   #body
   body=await request.json()
   table=body["table"]
   id=body["id"]
   column=body["column"]
   value=body["value"]
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
