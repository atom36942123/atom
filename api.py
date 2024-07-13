#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request

#router
from fastapi import APIRouter
router_database=APIRouter(tags=["database"])

#database
@router_database.get("/{x}/database-create")
async def function_api_database_create(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #table create
    for item in config_table:
        query=f"create table if not exists {item} (id bigint primary key generated always as identity);"
        response=await function_query_runner(postgres_object[x],"write",query,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column create
    for k,v in config_column.items():
        for table in v[1]:
            query=f"alter table {table} add column if not exists {k} {v[0]};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #final response
    return {"status":1,"message":"database create done"}


