#router
from fastapi import APIRouter
router=APIRouter(tags=["feed"])

#feed
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization
from function import function_add_creator_key
from function import function_add_action_count
from fastapi_cache.decorator import cache
from function import function_read_redis_key
@router.get("/{x}/feed/general")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_feed_general(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #prework
   query_param=dict(request.query_params)
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #where
   where_param={k:v for k,v in query_param.items() if k not in ["table","order","limit","page"]}
   where_param_values={k:v.split(',',1)[1] for k,v in where_param.items()}
   where_param_operator={k:v.split(',',1)[0] for k,v in where_param.items()}
   key_list=[f"({k} {where_param_operator[k]} :{k} or :{k} is null)" for k,v in where_param_values.items()]
   key_joined=' and '.join(key_list)
   where=f"where {key_joined}" if key_joined else ""
   #sanitization
   values_list=[where_param_values]
   response=await function_sanitization(request.state.postgres_object,values_list,"read")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #read object
   query=f"select * from {table} {where} order by {order} limit {limit} offset {(page-1)*limit};"
   values=values
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=[dict(item) for item in output]
   #add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add action count
   response=await function_add_action_count(request.state.postgres_object,output,table,"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}
