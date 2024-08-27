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

#bulk read
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
@router.get("/utility/bulk-read")
async def function_utility_bulk_read(request:Request,table:str,ids:str):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#create presigned url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_aws
@router.get("/utility/create-presigned-url")
async def function_create_presigned_url(request:Request,filename:str):
   #logic
   response=await function_aws("create_presigned_url",{"filename":filename})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#send email ses
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_aws
@router.post("/utility/send-email-ses")
async def function_send_email_ses(request:Request):
   #logic
   body=await request.json()
   response=await function_aws("send_email_ses",body)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#feed
from fastapi import Request
from config import postgres_object
from fastapi.responses import JSONResponse
from function import function_auth_check
from function import function_object_read
from fastapi_cache.decorator import cache
from function import function_read_redis_key
from function import function_add_creator_key,function_add_action_count
@router.get("/admin/feed")
async def function_admin_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth check
   response=await function_auth_check(request,"jwt",["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request query param
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","order","limit","page"]}
   response=await function_object_read(postgres_object,table,where_param_raw,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
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
