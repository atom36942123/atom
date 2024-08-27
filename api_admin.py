#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#qrunner
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/admin/qrunner")
async def function_admin_qrunner(request:Request,query:str):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=query
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return output

#database init
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_database_init
@router.get("/admin/database-init")
async def function_admin_database_init(request:Request):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":"done"}

#delete s3 url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_aws
@router.delete("/admin/delete-s3-url")
async def function_admin_delete_s3_url(request:Request,url:str):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_aws("delete_s3_url",{"url":url})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#delete s3 url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_aws
@router.delete("/admin/delete-s3-url")
async def function_admin_delete_s3_url(request:Request,url:str):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_aws("delete_s3_url",{"url":url})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#csv
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from fastapi import UploadFile
import csv,codecs
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
from function import function_object_create
from function import function_object_update
from function import function_sanitization
@router.post("/admin/csv-create",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_admin_csv_create(request:Request,mode:str,table:str,file:UploadFile):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   if file.content_type!="text/csv":return {"status":0,"message":"file must be csv"}
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   payload_list=[]
   for row in file_csv:payload_list.append(row)
   #logic
   if mode=="create":response=await function_object_create(postgres_object,table,payload_list,function_sanitization)
   if mode=="update":response=await function_object_update(postgres_object,table,payload_list,function_sanitization)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   await file.close()
   return response

#update cell
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from datetime import datetime
from function import function_sanitization
from fastapi.responses import JSONResponse
@router.put("/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   table=request_body["table"]
   id=request_body["id"]
   column=request_body["column"]
   value=request_body["value"]
   #function sanitization
   response=await function_sanitization("update",[{column:value}])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   value=response["message"][0][column]
   #logic
   query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
   query_param={"value":value,"id":id,"updated_at":datetime.now(),"updated_by_id":user['id']}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#delete bulk
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.delete("/admin/delete-bulk")
async def function_admin_delete_bulk(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #table check
   if table in ["users"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   #length check
   if len(ids)>10000:return JSONResponse(status_code=400,content=({"status":0,"message":"ids length exceeded"}))
   #logic
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#database clean
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.delete("/admin/database-clean")
async def function_admin_database_clean(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
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

#feed
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from function import function_prepare_where
from function import function_sanitization
from fastapi.responses import JSONResponse
@router.get("/admin/feed")
async def function_admin_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request query param
   request_query_param=dict(request.query_params)
   #prepare where
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_prepare_where(where_param_raw)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string=response["message"][0]
   where_param=response["message"][1]
   #query set
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   #sanitization query_param
   response=await function_sanitization("read",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#read bulk
from fastapi import Request
from config import postgres_object
from function import function_auth_check
from fastapi.responses import JSONResponse
@router.get("/admin/read-bulk")
async def function_admin_read_bulk(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
