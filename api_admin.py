#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#common
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_auth_check

#query runner
@router.get("/admin/query-runner")
async def function_admin_query_runner(request:Request,mode:str,query:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="single":
      query=query
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
   if mode=="bulk":
      for item in query.split("---"):
         query=item
         query_param={}
         output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#database clean
from function import function_database_clean
@router.delete("/admin/database-clean")
async def function_admin_database_clean(request:Request):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_database_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#csv
from fastapi import UploadFile
from function import function_file_to_object_list
from function import function_object_create
from function import function_object_update
@router.post("/admin/csv")
async def function_admin_csv(request:Request,mode:str,table:str,file:UploadFile):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await function_file_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
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
   response=await function_auth_check(postgres_object,request,["admin"])
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

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_auth_check
from config import postgres_object
from function import function_object_read
@router.get("/admin/object-read")
async def function_admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
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
   response=await function_auth_check(postgres_object,request,["admin"])
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
async def function_admin_bulk_delete(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(postgres_object,request,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids)>100:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   query=f"delete from {table} where id in ({ids});"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
