#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#database init
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_database_init
@router.get("/utility/database-init")
async def function_utility_database_init(request:Request):
   #logic
   response=await function_database_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#pcache
from fastapi import Request
from config import postgres_object
from fastapi_cache.decorator import cache
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
from fastapi.responses import JSONResponse
from config import postgres_object
from fastapi_cache.decorator import cache
from function import function_read_redis_key
@router.get("/utility/bulk-read")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_utility_bulk_read(request:Request,table:str,ids:str):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
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
