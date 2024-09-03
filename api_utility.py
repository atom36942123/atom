#search location
from fastapi import Request
from fastapi.responses import JSONResponse
from config import postgres_object
from function import function_search_location
@router.get("/utility/search-location")
async def function_utility_search_location(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content=({"status":0,"message":"table not allowed"}))
   request_query_param=dict(request.query_params)
   where_param_raw={k:v for k,v in request_query_param.items() if k not in ["table","location","within","order","limit","page"]}
   response=await function_search_location(postgres_object,table,where_param_raw,location,within,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response
