



@router.get("/{x}/database-alter")
async def function_api_database_alter(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
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
    #column default
    config_column_default={
    "created_at":["now()",config_table],
    "last_active_at":["now()",["users"]],
    "is_active":[1,["atom","users","post","comment","workseeker"]],
    "is_verified":[0,["atom","users","post","comment","workseeker"]],
    "is_pinned":[0,["post"]],
    }
    for column in schema_column:
        for k,v in config_column_default.items():
            for table in v[1]:
                if column["table_name"]==table and column["column_name"]==k and not column["column_default"]:
                    query=f"alter table {table} alter column {k} set default {v[0]};"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column checkin
    config_column_checkin={
    "is_active":[(0,1),["atom","users","post","comment","workseeker"]],
    "is_verified":[(0,1),["atom","users","post","comment","workseeker"]],
    "is_working":[(0,1),["workseeker"]],
    "is_pinned":[(0,1),["post"]],
    }
    for k,v in config_column_checkin.items():
        for table in v[1]:
            constraint_name=f"checkin_{k}_{table}"
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column nullable
    config_column_nullable={
    "created_by_id":["message"],
    "received_by_id":["message"],
    "parent_table":["likes","comment","bookmark","report","rating","block"],
    "parent_id":["likes","comment","bookmark","report","rating","block"],
    }
    for column in schema_column:
        for k,v in config_column_nullable.items():
            for table in v:
                if column["table_name"]==table and column["column_name"]==k and column["is_nullable"]=="YES":
                    query=f"alter table {table} alter column {k} set not null;"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #column unique
    config_column_unique={
    "username":["users"],
    "created_by_id,parent_table,parent_id":["likes","bookmark","report","block"],
    }
    for k,v in config_column_unique.items():
        for table in v:
            constraint_name=f"unique_{k.replace(',','_')}_{table}".replace(",","_")
            if constraint_name not in schema_constraint_name_list:
                query=f"alter table {table} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")    
    #finally
    return {"status":1,"message":"alter done"}

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
    "parent_table,parent_id":["default",["likes","comment","bookmark","report","rating","block"]],
    "is_active":["default",["atom","users","post","comment","workseeker"]],
    "is_verified":["default",["atom","users","post","comment","workseeker"]],
    "is_pinned":["default",["post"]],
    }
    #logic
    for k,v in config_column_index.items():
        for table in v[1]:
            index_name=f"index_{k.replace(',','_')}_{table}"
            query=f"create index if not exists {index_name} on {table}({k});"
            if v[0]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"index done"}

@router.get("/{x}/database-query")
async def function_api_database_query(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #config
    config_query={
    "create_root_user":"insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;",
    "rule_delete_disable_users_root":"create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;",
    }
    #logic
    for k,v in config_query.items():
        response=await function_query_runner(postgres_object[x],"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #finally
    return {"status":1,"message":"query done"}
