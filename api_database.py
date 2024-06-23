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
"is_admin":["int",["users"]],
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
"file_url":["text",["atom","post","s3"]],
"link_url":["text",["atom","post"]],"tag":["text[]",["atom","users","post","workseeker"]],
"number":["numeric",["post"]],
"date":["date",["post"]],
"status":["text",["post","report","message","helpdesk"]],
"remark":["text",["post","report","helpdesk"]],
"parent_table":["text",["likes","comment","bookmark","report","rating","block"]],
"parent_id":["bigint",["likes","comment","bookmark","report","rating","block"]],
"email":["text",["users","post","otp","helpdesk","workseeker"]],
"mobile":["text",["users","post","otp","helpdesk","workseeker"]],
"whatsapp":["text",["users","post","workseeker"]],
"phone":["text",["users","post"]],
"country":["text",["users","post"]],
"state":["text",["users","post"]],
"city":["text",["users","post"]],
"rating":["int",["rating","helpdesk"]],
"otp":["int",["otp"]],
"received_by_id":["bigint",["message"]],
"metadata":["jsonb",["post"]],
"profile":["text",["workseeker"]],
"college":["text",["workseeker"]],
"linkedin_url":["text",["workseeker"]],
"portfolio_url":["text",["workseeker"]],
"experience":["int",["workseeker"]],
"location_current":["text",["workseeker"]],
"location_expected":["text",["workseeker"]],
"salary_type":["text",["workseeker"]],
"salary_current":["int",["workseeker"]],
"salary_expected":["int",["workseeker"]],
"sector":["text",["workseeker"]],
"past_company_count":["int",["workseeker"]],
"is_working":["int",["workseeker"]],
"joining_days":["int",["workseeker"]],
}




config_column_unique={
"username":["users"],
"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"],
}

config_column_check_in={
"is_active":["(0,1)",["atom","users","post","comment"]],
"is_verified":["(0,1)",["atom","users","post","comment"]],
"is_admin":["(0,1)",["atom","users","post"]],
"is_working":["(0,1)",["workseeker"]],
}

config_column_index={
"created_at":["atom","users","post","message"],
"created_by_id":["atom","post","likes","comment","bookmark","report","rating","message"],
"parent_table":["likes","comment","bookmark","report","rating","block"],
"parent_id":["likes","comment","bookmark","report","rating","block"],
"received_by_id":["message"],
"description":["comment","message","helpdesk"],
"type":["atom","post","helpdesk"],
"password":["users"],
"firebase_id":["users"],
"email":["otp"],
"mobile":["otp"],
}
config_column_index_array={
"tag":["atom","users","post"],
}
config_query={
"rule_delete_disable_atom":"create or replace rule rule_delete_disable_atom as on delete to atom where old.is_admin=1 do instead nothing;",
"rule_delete_disable_post":"create or replace rule rule_delete_disable_post as on delete to post where old.is_admin=1 do instead nothing;",
"rule_delete_disable_users":"create or replace rule rule_delete_disable_users as on delete to users where old.is_admin=1 do instead nothing;",
"rule_delete_disable_root":"create or replace rule rule_delete_disable_root as on delete to users where old.id=1 do instead nothing;",
"index_comment_pp": "create index if not exists index_comment_pp on comment(parent_table,parent_id);",
}

#api
@router.get("/{x}/database")
async def api_func(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #create table
    for item in config_table:
        query=f"create table if not exists {item} (id bigint primary key generated always as identity);"
        response=await function_query_runner(postgres_object[x],"write",query,{})
        if response["status"]==0:return function_http_response(400,0,f"create_table_error={response['message']}+{query}")
    #create column
    for k,v in config_column.items():
        for item in v[1]:
            query=f"alter table {item} add column if not exists {k} {v[0]};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_add_error={response['message']}+{query}")
    #schema column
    query="select * from information_schema.columns where table_schema='public';"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_column=response["message"]
    #schema constraint
    query="select constraint_name from information_schema.constraint_column_usage;"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #created_at default
    for item in schema_column:
        if item["column_name"]=="created_at" and not item["column_default"]:
            query=f"alter table {item['table_name']} alter column created_at set default now();"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_default_error={response['message']}+{query}")
            
        
        
        

    

                    
    #column unique
    for k,v in config_column_unique.items():
        for item in v:
            constraint_name=f"unique_{k}_{item}".replace(",","_")
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {item} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"column_unique_error={response['message']}+{query}")
    #column check in
    for k,v in config_column_check_in.items():
        for item in v[1]:
            constraint_name=f"check_in_{k}_{item}"
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {item} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"column_check_in_error={response['message']}+{query}")
    #column index
    for k,v in config_column_index.items():
        for item in v:
            query=f"create index if not exists index_{k}_{item} on {item}({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_index_error={response['message']}+{query}")
    #column index array
    for k,v in config_column_index_array.items():
        for item in v:
            query=f"create index if not exists index_{k}_{item} on {item} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_index_array_error={response['message']}+{query}")
    #query
    for k,v in config_query.items():
        response=await function_query_runner(postgres_object[x],"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"query error={response['message']}")
    #create root user
    query="insert into users (username,password,is_admin) values (:username,:password,:is_admin) on conflict do nothing returning *;"
    values={"username":"root","password":"a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3","is_admin":1}
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,f"root_user_create_error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"done"}
