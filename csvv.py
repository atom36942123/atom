#router
from fastapi import APIRouter
router=APIRouter(tags=["csv"])

#create
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from fastapi import UploadFile
import csv,codecs 
from function import function_sanitization
@router.post("/{x}/csv/create",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv_create(request:Request,table:str,file:UploadFile):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   response=await function_sanitization(request.state.postgres_object,values_list,"create")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   #logic
   column_to_insert_list=[*values_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

#update
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
from function import function_sanitization
@router.put("/{x}/csv/update")
async def function_csv_update(request:Request,table:str,file:UploadFile):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
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
