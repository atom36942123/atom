#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#pcache
from fastapi import Request
from config import postgres_object
from fastapi_cache.decorator import cache
from function import function_read_redis_key
@router.get("/utility/pcache")
@cache(expire=60)
async def function_utility_pcache(request:Request):
   #logic
   config_pcache={"user_count":"select count(*) from users;"}
   temp={}
   for k,v in config_pcache.items():
      query=v
      query_param={}
      output=await postgres_object.fetch_all(query=query,values=query_param)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

#read bulk
from fastapi import Request
from config import postgres_object
@router.get("/utility/read-bulk")
async def function_utility_read_bulk(request:Request,table:str,ids:str):
   #logic
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#create presigned url
from fastapi import Request
from function import function_aws
@router.get("/utility/create-presigned-url")
async def function_create_presigned_url(request:Request,filename:str):
   #logic
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}









#feed
from fastapi import Request
from config import postgres_object
from fastapi_cache.decorator import cache
from function import function_read_redis_key
from function import function_prepare_where
from function import function_sanitization
from function import function_add_creator_key
from function import function_add_action_count
from fastapi.responses import JSONResponse
@router.get("/utility/feed")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_utility_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #table check
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
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
   #sanitization
   response=await function_sanitization("read",[query_param])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   query_param=response["message"][0]
   #query run
   output=await postgres_object.fetch_all(query=query,values=query_param)
   output=[dict(item) for item in output]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add action count
   response=await function_add_action_count(postgres_object,output,table,"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}


