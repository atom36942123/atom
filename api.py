#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request

#router
from fastapi import APIRouter
router=APIRouter()

#root
@router.get("/")
async def function_api_root():
   return {"status":1,"message":"welcome to atom"}

#database
@router.get("/{x}/database-create")
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

@router.get("/{x}/database-alter")
async def function_api_database_alter(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #read schema column
    response=await function_query_runner(postgres_object[x],"read",schema_column,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_column=response["message"]
    #read schema constraint
    response=await function_query_runner(postgres_object[x],"read",schema_constraint,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #default
    for column in schema_column:
        for k,v in config_column_default.items():
            for table in v[1]:
                if column["table_name"]==table and column["column_name"]==k and not column["column_default"]:
                    query=f"alter table {table} alter column {k} set default {v[0]};"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #checkin
    for k,v in config_column_checkin.items():
        for table in v[1]:
            constraint_name=f"checkin_{k}_{table}"
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #not nullable
    for column in schema_column:
        for k,v in config_column_not_nullable.items():
            for table in v:
                if column["table_name"]==table and column["column_name"]==k and column["is_nullable"]=="YES":
                    query=f"alter table {table} alter column {k} set not null;"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #unique
    for k,v in config_column_unique.items():
        for table in v:
            constraint_name=f"unique_{k.replace(',','_')}_{table}".replace(",","_")
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")    
    #finally
    return {"status":1,"message":"database alter done"}


