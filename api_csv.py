#router
from fastapi import APIRouter
router=APIRouter(tags=["csv"])

#create
from fastapi import Request
from config import postgres_object
from fastapi import UploadFile
import csv,codecs
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from function import function_token_check
from function import function_sanitization_query_param_list
from fastapi.responses import JSONResponse
@router.post("/csv/create",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv_create(request:Request,table:str,file:UploadFile):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if user["type"]!="admin":return JSONResponse(status_code=400,content={"status":0,"message":"admin issue"})
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content={"status":0,"message":"file extension issue"})
   #file read
   file_row_list=[]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   for row in file_csv:file_row_list.append(row)
   #column_to_insert_list
   column_to_insert_list=[*file_row_list[0]]
   #query set
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   #query_param set
   query_param_list=file_row_list
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"create",query_param_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param_list=response["message"]
   #query run
   output=await postgres_object.execute_many(query=query,values=query_param_list)
   #file close
   await file.close()
   #final
   return {"status":1,"message":output}

#update
from fastapi import Request
from config import postgres_object
from fastapi import UploadFile
import csv,codecs
from function import function_token_check
from function import function_sanitization_query_param_list
from fastapi.responses import JSONResponse
@router.put("/csv/update")
async def function_csv_update(request:Request,table:str,file:UploadFile):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content={"status":0,"message":"admin issue"})
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content={"status":0,"message":"file extension issue"})
   #file read
   file_row_list=[]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   for row in file_csv:file_row_list.append(row)
   #column_to_update_list
   column_to_update_list=[*file_row_list[0]]
   column_to_update_list.remove("id")
   #query set
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   #query_param set
   query_param_list=file_row_list
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"create",query_param_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param_list=response["message"]
   #query run
   output=await postgres_object.execute_many(query=query,values=query_param_list)
   #file close
   await file.close()
   #final
   return {"status":1,"message":output}


#read
from fastapi import Request
from config import postgres_object
from fastapi import UploadFile
import csv,codecs
from function import function_token_check
from fastapi.responses import JSONResponse
@router.get("/csv/read")
async def function_csv_read(request:Request,table:str,file:UploadFile):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content={"status":0,"message":"admin issue"})
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content={"status":0,"message":"file extension issue"})
   #file read
   file_row_list=[]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   for row in file_csv:file_row_list.append(row)
   #logic
   ids_list=[str(item["id"]) for item in file_row_list]
   ids_to_read=','.join(ids_list)
   query=f"select * from {table} where id in ({ids_to_read}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #file close
   await file.close()
   #final
   return {"status":1,"message":output}

#delete
from fastapi import Request
from config import postgres_object
from fastapi import UploadFile
import csv,codecs
from function import function_token_check
from fastapi.responses import JSONResponse
@router.delete("/csv/delete")
async def function_csv_delete(request:Request,table:str,file:UploadFile):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #admin check
   if user["type"]!="admin":return JSONResponse(status_code=400,content={"status":0,"message":"admin issue"})
   #file extension check
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content={"status":0,"message":"file extension issue"})
   #file read
   file_row_list=[]
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   for row in file_csv:file_row_list.append(row)
   #query set
   query=f"delete from {table} where id=:id;"
   query_param_list=file_row_list
   #sanitization query_param_list
   response=await function_sanitization_query_param_list(postgres_object,"create",query_param_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param_list=response["message"]
   #query run
   output=await postgres_object.execute_many(query=query,values=query_param_list)
   #file close
   await file.close()
   #final
   return {"status":1,"message":output}

