#router
from fastapi import APIRouter
router=APIRouter()

#env
from environs import Env
env=Env()
env.read_env()

#import
from fastapi import Request,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#config
config_database={
"created_at":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"timestamptz","now()",None,1],"created_by_id":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"bigint",None,None,1],"received_by_id":[["message"],"bigint",None,None,1],
"updated_at":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"timestamptz",None,None,0],"updated_by_id":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"bigint",None,None,0],"is_pinned":[["post"],"int",0,(0,1),1],
"is_active":[["atom","users","post","comment","workseeker"],"int",1,(0,1),1],"is_verified":[["atom","users","post","comment","workseeker"],"int",0,(0,1),1],
"parent_table":[["likes","comment","bookmark","report","rating","block"],"text",None,None,1],"parent_id":[["likes","comment","bookmark","report","rating","block"],"bigint",None,None,1],
"firebase_id":[["users"],"text",None,None,1],"google_id":[["users"],"text",None,None,1],
"last_active_at":[["users"],"timestamptz","now()",None,0],"otp":[["otp"],"int",None,None,1],"last_active_at":[["users"],"timestamptz","now()",None,0],
"username":[["users"],"text",None,None,1],"password":[["users"],"text",None,None,1],
"profile_pic_url":[["users"],"text",None,None,0],"date_of_birth":[["users"],"date",None,None,0],"name":[["users","workseeker"],"text",None,None,0],"gender":[["users","workseeker"],"text",None,None,0],
"email":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],"mobile":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],"whatsapp":[["users","post","workseeker"],"text",None,None,1],"phone":[["users","post","workseeker"],"text",None,None,1],
"country":[["users","post",],"text",None,None,1],"state":[["users","post"],"text",None,None,1],"city":[["users","post"],"text",None,None,1],
"type":[["post","atom","users","helpdesk"],"text",None,None,1],"title":[["post","atom","users"],"text",None,None,0],"description":[["post","atom","users","comment","report","rating","block","message","helpdesk","workseeker"],"text",None,None,0],"file_url":[["post","atom","file"],"text",None,None,0],"link_url":[["post","atom"],"text",None,None,0],"tag":[["post","atom","users","workseeker"],"text[]",None,None,1],
"number":[["post"],"numeric",None,None,0],"date":[["post"],"date",None,None,0],"status":[["post","report","message","helpdesk"],"text",None,None,1],"remark":[["post","report","helpdesk"],"text",None,None,0],"rating":[["post","rating","helpdesk"],"int",None,None,0],
"work_type":[["workseeker"],"text",None,None,1],"work_profile":[["workseeker"],"text",None,None,1],
"degree":[["workseeker"],"text",None,None,0],"college":[["workseeker"],"text",None,None,0],"linkedin_url":[["workseeker"],"text",None,None,0],"portfolio_url":[["workseeker"],"text",None,None,0],"experience":[["workseeker"],"int",None,None,1],"experience_work_profile":[["workseeker"],"int",None,None,0],"is_working":[["workseeker"],"int",None,(0,1),1],
"location_current":[["workseeker"],"text",None,None,1],"location_expected":[["workseeker"],"text",None,None,1],
"currency":[["workseeker"],"text",None,None,0],"salary_frequency":[["workseeker"],"text",None,None,0],"salary_current":[["workseeker"],"int",None,None,0],"salary_expected":[["workseeker"],"int",None,None,0],
"sector":[["workseeker"],"text",None,None,0],"past_company_count":[["workseeker"],"int",None,None,0],"past_company_name":[["workseeker"],"text",None,None,0],
"marital_status":[["workseeker"],"text",None,None,0],"physical_disability":[["workseeker"],"text",None,None,0],"hobby":[["workseeker"],"text",None,None,0],"language":[["workseeker"],"text",None,None,0],
"joining_days":[["workseeker"],"int",None,None,1],"career_break_month":[["workseeker"],"int",None,None,0],"resume_url":[["workseeker"],"text",None,None,0],"achievement":[["workseeker"],"text",None,None,0],"certificate":[["workseeker"],"text",None,None,0],"project":[["workseeker"],"text",None,None,0],"is_founder":[["workseeker"],"int",None,(0,1),1],"soft_skill":[["workseeker"],"text",None,None,0],"tool":[["workseeker"],"text",None,None,0],"achievement_work":[["workseeker"],"text",None,None,0],
}

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   return await request.state.postgres_object.fetch_all(query=query,values={})

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   #token
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #table
   for item in config_database["created_at"][0]:await request.state.postgres_object.fetch_all(query=f"create table if not exists {item} (id bigint primary key generated always as identity);",values={})
   #column
   return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"config_databae length issue"})) for k,v in config_database.items() if len(v)!=5
      
      for item in v[0]:await request.state.postgres_object.fetch_all(query=f"alter table {item} add column if not exists {k} {v[1]};",values={})
   #helper
   schema_column=await request.state.postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   #default
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column {k} set default {v[2]};",values={}) for k,v in config_database.items() for table in v[0] for column in schema_column if v[2] and column["column_name"]==k and column["table_name"]==table and not column["column_default"]]
   return {"status":1,"message":"done"}

    # #alter column checkin
    # for k,v in config_column.items():
    #     if v[3]:
    #         for table in v[0]:
    #             constraint_name=f"checkin_{k}_{table}"
    #             if constraint_name not in schema_constraint_name_list:
    #                 query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[3]});"
    #                 response=await function_query_runner(request.state.postgres_object,"write",query,{})
    #                 if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}") 
    # #add constraint
    # query_dict={
    # "unique_username_users":"alter table users add constraint unique_username_users unique (username);",
    # "unique_created_by_id_parent_table_parent_id_likes":"alter table likes add constraint unique_created_by_id_parent_table_parent_id_likes unique (created_by_id,parent_table,parent_id);",
    # "unique_created_by_id_parent_table_parent_id_bookmark":"alter table bookmark add constraint unique_created_by_id_parent_table_parent_id_bookmark unique (created_by_id,parent_table,parent_id);",
    # "unique_created_by_id_parent_table_parent_id_report":"alter table report add constraint unique_created_by_id_parent_table_parent_id_report unique (created_by_id,parent_table,parent_id);",
    # "unique_created_by_id_parent_table_parent_id_block":"alter table block add constraint unique_created_by_id_parent_table_parent_id_block unique (created_by_id,parent_table,parent_id);",
    # }
    # for k,v in query_dict.items():
    #     if k not in schema_constraint_name_list:
    #         response=await function_query_runner(request.state.postgres_object,"write",v,{})
    #         if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    # #misc query
    # query_dict={
    # "create_root_user":"insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;",
    # "rule_delete_disable_users_root":"create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;",
    # }
    # for k,v in query_dict.items():
    #     response=await function_query_runner(request.state.postgres_object,"write",v,{})
    #     if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    # #index
    # response=await function_drop_all_index(request.state.postgres_object,function_query_runner)
    # if response["status"]==0:return function_http_response(400,0,response["message"])
    # for k,v in config_column.items():
    #     if v[4]==1:
    #         for table in v[0]:
    #             index_name=f"index_{k}_{table}"
    #             query=f"create index if not exists {index_name} on {table}({k});"
    #             if v[1]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
    #             response=await function_query_runner(request.state.postgres_object,"write",query,{})
    #             if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")        
    # query_dict={
    # "index_parent_table_parent_id_likes":"create index if not exists index_parent_table_parent_id_likes on likes(parent_table,parent_id);",
    # "index_parent_table_parent_id_bookmark":"create index if not exists index_parent_table_parent_id_bookmark on bookmark(parent_table,parent_id);",
    # "index_parent_table_parent_id_comment":"create index if not exists index_parent_table_parent_id_comment on comment(parent_table,parent_id);",
    # }
    # for k,v in query_dict.items():
    #     response=await function_query_runner(request.state.postgres_object,"write",v,{})
    #     if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #final response
    

   
   
