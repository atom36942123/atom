#router
from fastapi import APIRouter
router=APIRouter(tags=["csv"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check root
from config import config_key_root

#import ratelimiter
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

#import file to csv converter
import csv
import codecs

#create
from fastapi import Request
from fastapi import UploadFile
from function import function_sanitization_query_param_list
@router.post("/{x}/csv/create",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv_create(request:Request,table:str,file:UploadFile):
   #database
   postgres_object=request.state.postgres_object
   #auth check root
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #file to csv
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   #column_to_insert_dict_list
   column_to_insert_dict_list=[]
   for row in file_csv:
      column_to_insert_dict_list.append(row)
   #query set
   column_to_insert_dict=column_to_insert_dict_list[0]
   query=f"insert into {table} ({','.join([*column_to_insert_dict])}) values ({','.join([':'+item for item in [*column_to_insert_dict]])}) returning *;"
   query_param_list=column_to_insert_dict_list
   #sanitization query_param
   response=await function_sanitization_query_param_list(postgres_object,"create",query_param_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   query_param_list=response["message"]
   #query run
   output=await postgres_object.execute_many(query=query,values=query_param_list)
   #final
   await file.close()
   return {"status":1,"message":output}





   
   column_to_update_dict=body
   column_to_update_dict["updated_at"]=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
   column_to_update_dict["updated_by_id"]=user["id"]
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in column_to_update_dict:column_to_update_dict.pop(item)
   #query set
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in [*column_to_update_dict]])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   query_param=column_to_update_dict|{"id":id,"created_by_id":user["id"]}
   if table=="users":query_param["id"],query_param["created_by_id"]=user["id"],None
   #sanitization query_param
   response=await function_sanitization_query_param_list(postgres_object,"update",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#update
from fastapi import Request
from fastapi import UploadFile
from function import function_sanitization_query_param_list
@router.put("/{x}/csv/update")
async def function_csv_update(request:Request,table:str,file:UploadFile):
   #database
   postgres_object=request.state.postgres_object
   #auth check root
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #file to csv
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   #column_to_update_dict_list
   column_to_update_dict_list=[]
   for row in file_csv:
      
      column_to_update_dict_list.append(row)
   
   
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   response=await function_sanitization(request.state.postgres_object,values_list,"update")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   #logic
   column_to_update_list=[item for item in [*values_list[0]] if item not in ["id"]]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

#read
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
@router.get("/{x}/csv/read")
async def function_csv_read(request:Request,table:str,file:UploadFile):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #logic
   ids_to_read=','.join([str(item["id"]) for item in values_list])
   query=f"select * from {table} where id in ({ids_to_read}) order by id desc;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   #final
   await file.close()
   return {"status":1,"message":output}

#delete
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
@router.delete("/{x}/csv/delete")
async def function_csv_delete(request:Request,table:str,file:UploadFile):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   for index,object in enumerate(values_list):
      for k,v in object.items():values_list[index][k]=int(v) if v else None
   #logic
   query=f"delete from {table} where id=:id;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}
