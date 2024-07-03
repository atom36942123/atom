#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request

#router
from fastapi import APIRouter
router=APIRouter(tags=["database"])

#config
config_table=["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","s3","otp","workseeker"]
config_column={
"created_at":["timestamptz",config_table],
"created_by_id":["bigint",config_table],
"updated_at":["timestamptz",["atom","users","post","comment","report","message","helpdesk","workseeker"]],
"updated_by_id":["bigint",["atom","users","post","comment","report","message","helpdesk","workseeker"]],
"is_active":["int",["atom","users","post","comment","workseeker"]],
"is_verified":["int",["atom","users","post","comment","workseeker"]],
"parent_table":["text",["likes","comment","bookmark","report","rating","block"]],
"parent_id":["bigint",["likes","comment","bookmark","report","rating","block"]],
"received_by_id":["bigint",["message"]],
"username":["text",["users"]],
"password":["text",["users"]],
"firebase_id":["text",["users"]],
"last_active_at":["timestamptz",["users"]],
"profile_pic_url":["text",["users"]],
"name":["text",["users","workseeker"]],
"gender":["text",["users","workseeker"]],
"date_of_birth":["date",["users"]],
"type":["text",["atom","users","post","helpdesk","workseeker"]],
"title":["text",["atom","users","post"]],
"description":["text",["atom","users","post","comment","report","rating","block","message","helpdesk","workseeker"]],
"file_url":["text",["atom","post","s3","workseeker"]],
"link_url":["text",["atom","post"]],
"tag":["text[]",["atom","users","post","workseeker"]],
"number":["numeric",["post"]],
"date":["date",["post"]],
"status":["text",["post","report","message","helpdesk"]],
"remark":["text",["post","report","helpdesk"]],
"email":["text",["users","post","otp","helpdesk","workseeker"]],
"mobile":["text",["users","post","otp","helpdesk","workseeker"]],
"whatsapp":["text",["users","post","workseeker"]],
"phone":["text",["users","post"]],
"country":["text",["users","post"]],
"state":["text",["users","post"]],
"city":["text",["users","post"]],
"rating":["int",["rating","helpdesk"]],
"otp":["int",["otp"]],
"metadata":["jsonb",["post"]],
"work_profile":["text",["workseeker"]],
"experience":["int",["workseeker"]],
"sector":["text",["workseeker"]],
"college":["text",["workseeker"]],
"linkedin_url":["text",["workseeker"]],
"portfolio_url":["text",["workseeker"]],
"location_current":["text",["workseeker"]],
"location_expected":["text",["workseeker"]],
"salary_type":["text",["workseeker"]],
"salary_current":["int",["workseeker"]],
"salary_expected":["int",["workseeker"]],
"past_company_count":["int",["workseeker"]],
"is_working":["int",["workseeker"]],
"joining_days":["int",["workseeker"]],
}
config_column_checkin={
"is_active":[(0,1),["atom","users","post","comment","workseeker"]],
"is_verified":[(0,1),["atom","users","post","comment","workseeker"]],
"is_working":[(0,1),["workseeker"]],
}
config_column_default={
"created_at":["now()",config_table],
"last_active_at":["now()",["users"]],
"is_active":[1,["atom","users","post","comment","workseeker"]],
"is_verified":[0,["atom","users","post","comment","workseeker"]],
}
config_column_nullable={
"created_by_id":["message"],
"received_by_id":["message"],
"parent_table":["likes","comment","bookmark","report","rating","block"],
"parent_id":["likes","comment","bookmark","report","rating","block"],
}
config_column_unique={
"username":["users"],
"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"],
}
config_query={
"create_root_user":"insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;",
"rule_delete_disable_users_root":"create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;",
"index_comment_parent":"create index if not exists index_comment_parent on comment(parent_table,parent_id);",
}

#api
@router.get("/{x}/database-reset")
async def function_api_database_reset(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #x check
    if x not in ["test"]:return function_http_response(400,0,"x not allowed")
    #drop all query
    query='''
    DO $$ DECLARE r RECORD;
    BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname=current_schema()) LOOP
    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; 
    END LOOP;
    END $$;
    '''
    #logic
    response=await function_query_runner(postgres_object[x],"write",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return {"status":1,"message":"reset done"}

@router.get("/{x}/database-init")
async def function_api_database_init(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #create table
    for item in config_table:
        query=f"create table if not exists {item} (id bigint primary key generated always as identity);"
        response=await function_query_runner(postgres_object[x],"write",query,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #create column
    for k,v in config_column.items():
        for table in v[1]:
            query=f"alter table {table} add column if not exists {k} {v[0]};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #read schema column
    query="select * from information_schema.columns where table_schema='public';"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_column=response["message"]
    #read schema constraint
    query="select constraint_name from information_schema.constraint_column_usage;"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #column checkin
    for k,v in config_column_checkin.items():
        for table in v[1]:
            constraint_name=f"checkin_{k}_{table}"
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column default
    for column in schema_column:
        for k,v in config_column_default.items():
            for table in v[1]:
                if column["table_name"]==table and column["column_name"]==k and not column["column_default"]:
                    query=f"alter table {table} alter column {k} set default {v[0]};"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column nullable
    for column in schema_column:
        for k,v in config_column_nullable.items():
            for table in v:
                if column["table_name"]==table and column["column_name"]==k and column["is_nullable"]=="YES":
                    query=f"alter table {table} alter column {k} set not null;"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column unique
    for k,v in config_column_unique.items():
        for table in v:
            constraint_name=f"unique_{k}_{table}".replace(",","_")
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")    
    #query
    for k,v in config_query.items():
        response=await function_query_runner(postgres_object[x],"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #finally
    return {"status":1,"message":"database init done"}

@router.get("/{x}/database-index")
async def function_api_database_index(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #drop all index
    response=await function_drop_all_index(postgres_object[x],function_query_runner)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #mapping
    config_column_index={
    "created_at":["default",["atom","users","post","message"]],
    "created_by_id":["default",["atom","post","likes","comment","bookmark","report","rating","message"]],
    "parent_table":["default",["likes","comment","bookmark","report","rating","block"]],
    "parent_id":["default",["likes","comment","bookmark","report","rating","block"]],
    "received_by_id":["default",["message"]],
    "description":["default",["comment","message","helpdesk"]],
    "type":["default",["atom","post","helpdesk","users"]],
    "password":["default",["users"]],
    "firebase_id":["default",["users"]],
    "email":["default",["otp"]],
    "mobile":["default",["otp"]],
    "tag":["array",["atom","users","post"]],
    }
    #logic
    for k,v in config_column_index.items():
        for table in v[1]:
            index_name=f"index_{k}_{table}"
            query=f"create index if not exists {index_name} on {table}({k});"
            if v[0]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"reset done"}
