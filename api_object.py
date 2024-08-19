#router
from fastapi import APIRouter
router=APIRouter(tags=["object"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check jwt
from config import config_key_jwt
import jwt
import json

#create
from fastapi import Request
from function import function_sanitization
@router.post("/{x}/object/create")
async def function_object_create(request:Request,table:str):
   #database 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #table check
   if table in ["users","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body
   body=await request.json()
   #create object query
   column_to_insert_dict={}
   query=f"insert into {table} ({','.join([*column_to_insert_dict])}) values ({','.join([':'+item for item in [*column_to_insert_dict]])}) returning *;"
   query_param=column_to_insert_dict
   #prepare column_to_insert_dict
   column_to_insert_dict=body
   column_to_insert_dict["created_by_id"]=user["id"]
   #remove now allowed keys
   config_column_create_not_allowed=["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]
   for k,v in column_to_insert_dict.items():
      if k in config_column_create_not_allowed:column_to_insert_dict.pop(k)
   #sanitization
   values_list=[column_to_insert_dict]
   response=await function_sanitization("create",postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   column_to_insert_dict=values_list[0]
   #logic
   values=column_to_insert_dict
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#update
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from function import function_sanitization
@router.put("/{x}/object/update")
async def function_object_update(request:Request,table:str,id:int):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #body
   body=await request.json()
   #query set
   column_to_update_list=[item for item in [*body] if item not in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
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
   #logic
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   values=values_list[0]
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/object/delete")
async def function_object_delete(request:Request,table:str,id:int):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={}
   values["id"]=user["id"] if table=="users" else id
   values["created_by_id"]=None if table=="users" else user["id"]
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#read
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization
from function import function_prepare_where
@router.get("/{x}/object/read")
async def function_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #query param
   query_param=dict(request.query_params)
   #where
   where_param={k:v for k,v in query_param.items() if k not in ["table","order","limit","page"]}|{"created_by_id":f"=,{user['id']}"}
   response=await function_prepare_where(where_param)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   where=response["message"][0]
   values=response["message"][1]
   #sanitization
   values_list=[values]
   response=await function_sanitization(request.state.postgres_object,values_list,"read")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   #read object
   query=f"select * from {table} {where} order by {order} limit {limit} offset {(page-1)*limit};"
   values=values_list[0]
   output=await postgres_object.fetch_all(query=query,values=query_param)
   output=[dict(item) for item in output]
   #final
   return {"status":1,"message":output}
