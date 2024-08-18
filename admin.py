#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#update cell
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from function import function_sanitization
@router.put("/{x}/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   #body
   body=await request.json()
   table=body["table"]
   id=body["id"]
   column=body["column"]
   value=body["value"]
   #sanitization
   values_list=[{column:value}]
   response=await function_sanitization(request.state.postgres_object,values_list,"update")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   value=values_list[0][column]
   #logic
   query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
   values={"value":value,"id":id,"updated_at":datetime.now(),"updated_by_id":user['id']}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
