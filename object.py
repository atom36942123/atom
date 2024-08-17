#router
from fastapi import APIRouter
router=APIRouter(tags=["object"])

#create object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization
@router.post("/{x}/my/create-object")
async def function_my_create_object(request:Request,table:str):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if table in ["users","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   body=await request.json()
   #query set
   column_to_insert_list=[item for item in [*body] if item not in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]]+["created_by_id"]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   #values
   values={}
   for item in column_to_insert_list:values[item]=None
   #values assign
   for k,v in values.items():
      if k in body:values[k]=body[k]
   values["created_by_id"]=user["id"]
   #sanitization
   values_list=[values]
   response=await function_sanitization(request.state.postgres_object,values_list,"create")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#update object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from function import function_sanitization
@router.put("/{x}/my/update-object")
async def function_my_update_object(request:Request,table:str,id:int):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #query set
   column_to_update_list=[item for item in [*body] if item not in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   #values
   values={}
   for item in column_to_update_list:values[item]=None
   values["id"]=None
   values["created_by_id"]=None
   #values assign
   for k,v in values.items():
      if k in body:values[k]=body[k]
   values["updated_at"]=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
   values["updated_by_id"]=user["id"]
   values["id"]=user["id"] if table=="users" else id
   values["created_by_id"]=None if table=="users" else user["id"]
   #sanitization
   values_list=[values]
   response=await function_sanitization(request.state.postgres_object,values_list,"update")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #query run
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#delete object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/my/delete-object")
async def function_my_delete_object(request:Request,table:str,id:int):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={}
   values["id"]=user["id"] if table=="users" else id
   values["created_by_id"]=None if table=="users" else user["id"]
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#read object
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization
@router.get("/{x}/my/read-object")
async def function_my_read_object(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   query_param=dict(request.query_params)
   #where
   query_param["created_by_id"]=f"=,{user['id']}"
   where_param={k:v for k,v in query_param.items() if k not in ["table","order","limit","page"]}
   where_param_values={k:v.split(',',1)[1] for k,v in where_param.items()}
   where_param_operator={k:v.split(',',1)[0] for k,v in where_param.items()}
   key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param_values.items()]
   key_joined=' and '.join(key_list)
   where=f"where {key_joined}" if key_joined else ""
   #sanitization
   values_list=[where_param_values]
   response=await function_sanitization(request.state.postgres_object,values_list,"read")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #read object
   query=f"select * from {table} {where} order by {order} limit {limit} offset {(page-1)*limit};"
   values=values
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=[dict(item) for item in output]
   #final
   return {"status":1,"message":output}
