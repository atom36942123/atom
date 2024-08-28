#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#query runner
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
@router.get("/admin/query-runner")
async def function_admin_query_runner(request:Request,query:str,mode:str=None):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if not mode:
      query=query
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#database init
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
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
   return response

#database clean
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from function import function_database_clean
@router.delete("/admin/database-clean")
async def function_admin_database_clean(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_database_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#csv
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from fastapi import UploadFile
import csv,codecs
from function import function_object_create
from function import function_object_update
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends
@router.post("/admin/csv",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_admin_csv(request:Request,mode:str,table:str,file:UploadFile):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   if file.content_type!="text/csv":return {"status":0,"message":"file extension must be csv"}
   file_csv=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   object_list=[]
   for row in file_csv:object_list.append(row)
   await file.close()
   #logic
   if mode=="create":response=await function_object_create(postgres_object,table,object_list)
   if mode=="update":response=await function_object_update(postgres_object,table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#update cell
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from function import function_object_update
@router.put("/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   request_body=await request.json()
   table,id,column,value=request_body["table"],request_body["id"],request_body["column"],request_body["value"]
   object={"id":id,column:value,"updated_by_id":user["id"]}
   response=await function_object_update(postgres_object,table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#feed
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from function import function_object_read
@router.get("/admin/feed")
async def function_admin_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request query param
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_object_read(postgres_object,table,where_param_raw,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#bulk read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
@router.get("/admin/bulk-read")
async def function_admin_bulk_read(request:Request,table:str,ids:str):
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

#bulk delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
@router.delete("/admin/bulk-delete")
async def function_admin_bulk_delete(request:Request,mode:str,table:str,ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   if len(ids)>100:return JSONResponse(status_code=400,content=({"status":0,"message":"ids length exceeded"}))
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
   
#delete s3 url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
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

#empty s3 bucket
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from function import function_aws
@router.delete("/admin/empty-s3-bucket")
async def function_admin_empty_s3_bucket(request:Request):
   #auth check
   response=await function_auth_check(request,"root",[])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_aws("empty_s3_bucket",{})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}
