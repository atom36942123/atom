#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#database init
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_database_init
from config import config_key_root
@router.get("/utility/database-init")
async def function_utility_database_init(request:Request):
   #auth check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
   #logic
   response=await function_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#project cache
from fastapi import Request
from config import postgres_object
from fastapi_cache.decorator import cache
@router.get("/utility/project-cache")
@cache(expire=60)
async def function_utility_project_cache(request:Request):
   #logic
   query_dict={
   "user_count":"select count(*) from users;"
   }
   temp={}
   for k,v in query_dict.items():
      query=v
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_object_read
from function import function_add_creator_key
from fastapi_cache.decorator import cache
from function import function_redis_key_builder
@router.get("/utility/object-read")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_utility_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_object_read(postgres_object,table,where_param_raw,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}

#bulk read
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
@router.get("/utility/bulk-read")
async def function_utility_bulk_read(request:Request,table:str,ids:str):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#location query
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_location_query
@router.get("/utility/location-query")
async def function_utility_location_query(request:Request,table:str,lat:float,long:float,min_meter:int,max_meter:int,order:str="id desc",limit:int=100,page:int=1):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   response=await function_location_query(postgres_object,table,lat,long,min_meter,max_meter,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
