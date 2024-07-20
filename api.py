#router
from fastapi import APIRouter
router=APIRouter()

#env
from environs import Env
env=Env()
env.read_env()

#import
from function import *
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

#schema
class schema_atom(BaseModel):
    id:int|None=None
    created_at:datetime|None=None
    created_by_id:int|None=None
    updated_at:datetime|None=None
    updated_by_id:int|None=None
    is_active:int|None=None
    is_verified:int|None=None
    parent_table:str|None=None
    parent_id:int|None=None
    received_by_id:int|None=None
    last_active_at:datetime|None=None
    firebase_id:str|None=None
    google_id:str|None=None
    otp:int|None=None
    metadata:dict|None=None
    username:str|None=None
    password:str|None=None
    profile_pic_url:str|None=None
    date_of_birth:datetime|None=None
    name:str|None=None
    gender:str|None=None
    email:str|None=None
    mobile:str|None=None
    whatsapp:str|None=None
    phone:str|None=None
    country:str|None=None
    state:str|None=None
    city:str|None=None
    type:str|None=None
    title:str|None=None
    description:str|None=None
    file_url:str|None=None
    link_url:str|None=None
    tag:list|None=None
    number:float|None=None
    date:datetime|None=None
    status:str|None=None
    remark:str|None=None
    rating:int|None=None
    is_pinned:int|None=None
    work_type:str|None=None
    work_profile:str|None=None
    degree:str|None=None
    college:str|None=None
    linkedin_url:str|None=None
    portfolio_url:str|None=None
    experience:int|None=None
    experience_work_profile:int|None=None
    is_working:int|None=None
    location_current:str|None=None
    location_expected:str|None=None
    currency:str|None=None
    salary_frequency:str|None=None
    salary_current:int|None=None
    salary_expected:int|None=None
    sector:str|None=None
    past_company_count:int|None=None
    past_company_name:str|None=None
    marital_status:str|None=None
    physical_disability:str|None=None
    hobby:str|None=None
    language:str|None=None
    joining_days:int|None=None
    career_break_month:int|None=None
    resume_url:str|None=None
    achievement:str|None=None
    certificate:str|None=None
    project:str|None=None
    is_founder:int|None=None
    soft_skill:str|None=None
    tool:str|None=None
    achievement_work:str|None=None

#database
@router.get("/{x}/database")
async def function_database(request:Request):
    #token check
    if request.headers.get("token")!=env("key"):return function_http_response(400,0,"env key issue")
    #config
    config_table=["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"]
    config_column={
    "created_at":[config_table,"timestamptz","now()",None,1],
    "created_by_id":[config_table,"bigint",None,None,1],
    "updated_at":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"timestamptz",None,None,0],
    "updated_by_id":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"bigint",None,None,0],
    "is_active":[["atom","users","post","comment","workseeker"],"int",1,(0,1),1],
    "is_verified":[["atom","users","post","comment","workseeker"],"int",0,(0,1),1],
    "parent_table":[["likes","comment","bookmark","report","rating","block"],"text",None,None,1],
    "parent_id":[["likes","comment","bookmark","report","rating","block"],"bigint",None,None,1],
    "received_by_id":[["message"],"bigint",None,None,1],
    "last_active_at":[["users"],"timestamptz","now()",None,0],
    "firebase_id":[["users"],"text",None,None,1],
    "google_id":[["users"],"text",None,None,1],
    "otp":[["otp"],"int",None,None,1],
    "metadata":[["post"],"jsonb",None,None,0],
    "username":[["users"],"text",None,None,1],
    "password":[["users"],"text",None,None,1],
    "profile_pic_url":[["users"],"text",None,None,0],
    "date_of_birth":[["users"],"date",None,None,0],
    "name":[["users","workseeker"],"text",None,None,0],
    "gender":[["users","workseeker"],"text",None,None,0],
    "email":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],
    "mobile":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],
    "whatsapp":[["users","post","workseeker"],"text",None,None,1],
    "phone":[["users","post","workseeker"],"text",None,None,1],
    "country":[["users","post",],"text",None,None,1],
    "state":[["users","post"],"text",None,None,1],
    "city":[["users","post"],"text",None,None,1],
    "type":[["post","atom","users","helpdesk"],"text",None,None,1],
    "title":[["post","atom","users"],"text",None,None,0],
    "description":[["post","atom","users","comment","report","rating","block","message","helpdesk","workseeker"],"text",None,None,0],
    "file_url":[["post","atom","file"],"text",None,None,0],
    "link_url":[["post","atom"],"text",None,None,0],
    "tag":[["post","atom","users","workseeker"],"text[]",None,None,1],
    "number":[["post"],"numeric",None,None,0],
    "date":[["post"],"date",None,None,0],
    "status":[["post","report","message","helpdesk"],"text",None,None,1],
    "remark":[["post","report","helpdesk"],"text",None,None,0],
    "rating":[["post","rating","helpdesk"],"int",None,None,0],
    "is_pinned":[["post"],"int",0,(0,1),1],
    "work_type":[["workseeker"],"text",None,None,1],
    "work_profile":[["workseeker"],"text",None,None,1],
    "degree":[["workseeker"],"text",None,None,0],
    "college":[["workseeker"],"text",None,None,0],
    "linkedin_url":[["workseeker"],"text",None,None,0],
    "portfolio_url":[["workseeker"],"text",None,None,0],
    "experience":[["workseeker"],"int",None,None,1],
    "experience_work_profile":[["workseeker"],"int",None,None,0],
    "is_working":[["workseeker"],"int",None,(0,1),1],
    "location_current":[["workseeker"],"text",None,None,1],
    "location_expected":[["workseeker"],"text",None,None,1],
    "currency":[["workseeker"],"text",None,None,0],
    "salary_frequency":[["workseeker"],"text",None,None,0],
    "salary_current":[["workseeker"],"int",None,None,0],
    "salary_expected":[["workseeker"],"int",None,None,0],
    "sector":[["workseeker"],"text",None,None,0],
    "past_company_count":[["workseeker"],"int",None,None,0],
    "past_company_name":[["workseeker"],"text",None,None,0],
    "marital_status":[["workseeker"],"text",None,None,0],
    "physical_disability":[["workseeker"],"text",None,None,0],
    "hobby":[["workseeker"],"text",None,None,0],
    "language":[["workseeker"],"text",None,None,0],
    "joining_days":[["workseeker"],"int",None,None,1],
    "career_break_month":[["workseeker"],"int",None,None,0],
    "resume_url":[["workseeker"],"text",None,None,0],
    "achievement":[["workseeker"],"text",None,None,0],
    "certificate":[["workseeker"],"text",None,None,0],
    "project":[["workseeker"],"text",None,None,0],
    "is_founder":[["workseeker"],"int",None,(0,1),1],
    "soft_skill":[["workseeker"],"text",None,None,0],
    "tool":[["workseeker"],"text",None,None,0],
    "achievement_work":[["workseeker"],"text",None,None,0],
    }
    #config_column length validation
    for k,v in config_column.items():
        if len(v)!=5:return function_http_response(400,0,f"config_column value length error={k}")
    #create table
    for item in config_table:
        query=f"create table if not exists {item} (id bigint primary key generated always as identity);"
        response=await function_query_runner(request.state.postgres_object,"write",query,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #create column
    for k,v in config_column.items():
        for table in v[0]:
            query=f"alter table {table} add column if not exists {k} {v[1]};"
            response=await function_query_runner(request.state.postgres_object,"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #read schema column
    query="select * from information_schema.columns where table_schema='public';"
    response=await function_query_runner(request.state.postgres_object,"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_column=response["message"]
    #read schema constraint
    query="select constraint_name from information_schema.constraint_column_usage;"
    response=await function_query_runner(request.state.postgres_object,"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    schema_constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #alter column default
    for k,v in config_column.items():
        if v[2]:
            for table in v[0]:
                for column in schema_column:
                    if column["column_name"]==k and column["table_name"]==table and not column["column_default"]:
                        query=f"alter table {table} alter column {k} set default {v[2]};"
                        response=await function_query_runner(request.state.postgres_object,"write",query,{})
                        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")                
    #alter column checkin
    for k,v in config_column.items():
        if v[3]:
            for table in v[0]:
                constraint_name=f"checkin_{k}_{table}"
                if constraint_name not in schema_constraint_name_list:
                    query=f"alter table {table} add constraint {constraint_name} check ({k} in {v[3]});"
                    response=await function_query_runner(request.state.postgres_object,"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}") 
    #add constraint
    query_dict={
    "unique_username_users":"alter table users add constraint unique_username_users unique (username);",
    "unique_created_by_id_parent_table_parent_id_likes":"alter table likes add constraint unique_created_by_id_parent_table_parent_id_likes unique (created_by_id,parent_table,parent_id);",
    "unique_created_by_id_parent_table_parent_id_bookmark":"alter table bookmark add constraint unique_created_by_id_parent_table_parent_id_bookmark unique (created_by_id,parent_table,parent_id);",
    "unique_created_by_id_parent_table_parent_id_report":"alter table report add constraint unique_created_by_id_parent_table_parent_id_report unique (created_by_id,parent_table,parent_id);",
    "unique_created_by_id_parent_table_parent_id_block":"alter table block add constraint unique_created_by_id_parent_table_parent_id_block unique (created_by_id,parent_table,parent_id);",
    }
    for k,v in query_dict.items():
        if k not in schema_constraint_name_list:
            response=await function_query_runner(request.state.postgres_object,"write",v,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #misc query
    query_dict={
    "create_root_user":"insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;",
    "rule_delete_disable_users_root":"create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(request.state.postgres_object,"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #index
    response=await function_drop_all_index(request.state.postgres_object,function_query_runner)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    for k,v in config_column.items():
        if v[4]==1:
            for table in v[0]:
                index_name=f"index_{k}_{table}"
                query=f"create index if not exists {index_name} on {table}({k});"
                if v[1]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
                response=await function_query_runner(request.state.postgres_object,"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")        
    query_dict={
    "index_parent_table_parent_id_likes":"create index if not exists index_parent_table_parent_id_likes on likes(parent_table,parent_id);",
    "index_parent_table_parent_id_bookmark":"create index if not exists index_parent_table_parent_id_bookmark on bookmark(parent_table,parent_id);",
    "index_parent_table_parent_id_comment":"create index if not exists index_parent_table_parent_id_comment on comment(parent_table,parent_id);",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(request.state.postgres_object,"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #final response
    return {"status":1,"message":"done"}

#signup
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   #body
   body=await request.json()
   if any(item not in body for item in ["username","password"]):return function_http_response(400,0,"username/password must")
   if any(not body[item] for item in ["username","password"]):return function_http_response(400,0,"username/password cant be null")
   #read user
   response=await function_query_runner(request.state.postgres_object,"read","select * from users where username=:username;",{"username":body["username"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if response["message"]:return function_http_response(400,0,"username already exist")
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   response=await function_query_runner(request.state.postgres_object,"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.post("/{x}/login")
async def function_login(x:str,request:Request):
   #body
   body=await request.json()
   #opt verify
   response=None
   if all(item in body for item in ["otp","email"]):response=await function_query_runner(request.state.postgres_object,"read","select * from otp where email=:email order by id desc limit 1;",{"email":body["email"]})
   if all(item in body for item in ["otp","mobile"]):response=await function_query_runner(request.state.postgres_object,"read","select * from otp where mobile=:mobile order by id desc limit 1;",{"mobile":body["mobile"]})
   if response:
       if response["status"]==0:return function_http_response(400,0,response["message"])
       if not response["message"]:return function_http_response(400,0,"otp not exist")
       if response["message"][0]["otp"]!=body["otp"]:return function_http_response(400,0,"otp mismatched")
   #read user
   if all(item in body for item in ["username","password"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where username=:username and password=:password;",{"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})
   if all(item in body for item in ["firebase_id"]):respomse=await function_query_runner(request.state.postgres_object,"read","select * from users where firebase_id=:firebase_id order by id desc limit 1;",{"firebase_id":hashlib.sha256(body["firebase_id"].encode()).hexdigest()})
   if all(item in body for item in ["email","otp"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where email=:email order by id desc limit 1;",{"email":body["email"]})
   if all(item in body for item in ["mobile","otp"]):response=await function_query_runner(request.state.postgres_object,"read","select * from users where mobile=:mobile order by id desc limit 1;",{"mobile":body["mobile"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   user=None if not response["message"] else response["message"][0]
   #not user
   if all(item in body for item in ["username","password"]) and not user:return function_http_response(400,0,"no such user")
   if all(item in body for item in ["firebase_id"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (firebase_id) values (:firebase_id) returning *;",{"firebase_id":hashlib.sha256(body["firebase_id"].encode()).hexdigest()})
   if all(item in body for item in ["email","otp"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (email) values (:email) returning *;",{"email":body["email"]})
   if all(item in body for item in ["mobile","otp"]) and not user:response=await function_query_runner(request.state.postgres_object,"write","insert into users (mobile) values (:mobile) returning *;",{"mobile":body["mobile"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #read user
   if not user:
       response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":response["message"]})
       if response["status"]==0:return function_http_response(400,0,response["message"])
       user=response["message"][0]
   #token encode
   data=json.dumps({"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
   response=await function_token_encode(data,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response
    
@router.get("/{x}/my-profile")
async def function_my_profile(request:Request,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #read user
    response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return function_http_response(400,0,"no user exist for token passed")
    user=response["message"][0]
    #extra key
    query_dict={
    "post_count":"select count(*) as number from post where created_by_id=:user_id;",
    "comment_count":"select count(*) as number from comment where created_by_id=:user_id;",
    "message_unread_count":"select count(*) as number from message where received_by_id=:user_id and status='unread';",
    "like_post_count":"select count(*) as number from likes where created_by_id=:user_id and parent_table='post';",
    "bookmark_post_count":"select count(*) as number from bookmark where created_by_id=:user_id and parent_table='post';",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(request.state.postgres_object,"read",v,{"user_id":request_user["id"]})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        user[k]=response["message"][0]["number"]
    #background task
    background_tasks.add_task(function_query_runner,request.state.postgres_object,"write","update users set last_active_at=:last_active_at where id=:id;",{"last_active_at":datetime.now(),"id":user["id"]})
    #final response
    return {"status":1,"message":user}

@router.get("/{x}/my-action-check")
async def function_my_action_check(request:Request,action:str,table:str,ids:str):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #ids into list
    if not ids:return function_http_response(400,0,f"ids cant be null")
    try:ids=[int(x) for x in ids.split(',')]
    except Exception as e:return function_http_response(400,0,e.args)
    #logic
    query=f"select parent_id from {action} join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
    values={"parent_table":table,"created_by_id":request_user["id"]}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #parent ids join
    try:ids_filtered=list(set([item["parent_id"] for item in response["message"] if item["parent_id"]]))
    except Exception as e:return function_http_response(400,0,e.args)
    #final response
    return {"status":1,"message":ids_filtered}

@router.get("/{x}/my-read-parent/{table}/{parent_table}/{page}")
async def function_my_read_parent(request:Request,table:str,parent_table:str,page:int):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #read parent ids
    limit=30
    offset=(page-1)*limit
    query=f"select parent_id from {table} where created_by_id=:created_by_id and parent_table=:parent_table order by id desc offset {offset} limit {limit};"
    values={"created_by_id":request_user["id"],"parent_table":parent_table}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    parent_ids=[x["parent_id"] for x in response["message"]]
    #read parent ids objects
    query=f"select * from {parent_table} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
    response=await function_query_runner(request.state.postgres_object,"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add like count
    response=await function_add_like_count(request.state.postgres_object,function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add comment count
    response=await function_add_comment_count(request.state.postgres_object,function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return response

@router.get("/{x}/my-message-inbox/{page}")
async def function_my_message_inbox(request:Request,page:int,is_unread:int=None):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    limit=30
    offset=(page-1)*limit
    query='''with mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),x as (select owner_id,max(id) as id from mcr group by owner_id offset :offset limit :limit),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by id desc;'''
    if is_unread==1:query='''with mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),x as (select owner_id,max(id) as id from mcr group by owner_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where received_by_id=:received_by_id and status='unread' order by id desc offset :offset limit :limit;'''
    values={"created_by_id":request_user['id'],"received_by_id":request_user['id'],"offset":offset,"limit":limit}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"received_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return response

@router.get("/{x}/my-message-thread/{user_id}/{page}")
async def function_my_message_thread(request:Request,user_id:int,page:int,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    limit=30
    offset=(page-1)*limit
    query=f"select * from message where (created_by_id=:user_1 and received_by_id=:user_2) or (created_by_id=:user_2 and received_by_id=:user_1) order by id desc offset {offset} limit {limit}"
    values={"user_1":request_user["id"],"user_2":user_id}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"received_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #background task
    query=f"update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where received_by_id=:received_by_id and created_by_id=:created_by_id returning *;"
    values={"status":"read","updated_by_id":request_user['id'],"updated_at":datetime.now(),"received_by_id":request_user['id'],"created_by_id":user_id}
    background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",query,values)
    #final response
    return response

@router.delete("/{x}/my-delete")
async def function_my_delete(request:Request,x:str,background_tasks:BackgroundTasks,mode:Literal["post_all","comment_all","message_all","like_post_all","bookmark_post_all","message","message_thread","like_post","bookmark_post","account"],user_id:int=None,post_id:int=None,message_id:int=None):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #refresh request_user
    response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return function_http_response(400,0,"no user for token passed")
    request_user=response["message"][0]
    #query set
    if mode=="comment_all":query,values="delete from comment where created_by_id=:created_by_id;",{"created_by_id":request_user['id']}
    if mode=="message_all":query,values="delete from message where created_by_id=:created_by_id or received_by_id=:received_by_id;",{"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="like_post_all":query,values="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table;",{"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="bookmark_post_all":query,values="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table;",{"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="message_thread":query,values="delete from message where (created_by_id=:a and received_by_id=:b) or (created_by_id=:b and received_by_id=:a);",{"a":request_user['id'],"b":user_id}   
    if mode=="like_post":query,values="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;",{"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    if mode=="bookmark_post":query,values="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;",{"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    if mode=="message":query,values=f"delete from message where id=:id and (created_by_id=:created_by_id or received_by_id=:received_by_id);",{"id":message_id,"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="post_all":
        if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"user type not allowed")
        query,values="delete from post where created_by_id=:created_by_id;",{"created_by_id":request_user['id']}
    if mode=="account":
        if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"not allowed")
        query,values="delete from users where id=:id;",{"id":request_user['id']}
        for item in ["post","likes","bookmark","report","rating","comment","block"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where created_by_id=:created_by_id;",{"created_by_id":request_user['id']})
        for item in ["message"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where created_by_id=:created_by_id or received_by_id=:received_by_id;",{"created_by_id":request_user['id'],"received_by_id":request_user['id']})
        for item in ["likes","bookmark","comment","rating","block","report"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where parent_table='users' and parent_id=:parent_id;",{"parent_id":request_user['id']})
    #query run
    response=await function_query_runner(request.state.postgres_object,"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return {"status":1,"message":"object deleted"}

@router.post("/{x}/object-create/{table}")
async def function_object_create(table:str,request:Request,body:schema_atom):
   #token check
   if table not in ["helpdesk","workseeker"] or request.headers.get("token"):
      response=await function_token_decode(request,env("key"))
      if response["status"]==0:return function_http_response(400,0,response["message"])
      request_user=response["message"]
   else:request_user,request_user["id"]={},None
   #param
   param={k: v for k, v in vars(body).items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"body cant be null")
   if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
   if "number" in param:param["number"]=round(param["number"],5)
   param["created_by_id"]=request_user["id"]
   if table=="message":param["status"]="unread"
   #logic
   query=f'''insert into {table} ({",".join([*param])}) values ({",".join([":"+item for item in [*param]])}) returning *;'''
   response=await function_query_runner(request.state.postgres_object,"write",query,param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.put("/{x}/object-update/{table}/{id}")
async def function_object_update(request:Request,table:str,id:int,body:schema_atom):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #refresh request_user
   response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   request_user=response["message"][0]
   #param
   param={k: v for k, v in vars(body).items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"body cant be null")
   if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
   if "number" in param:param["number"]=round(param["number"],5)
   param["updated_at"],param["updated_by_id"]=datetime.now(),request_user["id"]
   #non admin case
   id,created_by_id=id,None
   if request_user["type"] not in ["root","admin"]:
      if table=="users":id,created_by_id=request_user['id'],None
      else:id,created_by_id=id,request_user['id']
      for item in ["created_at","created_by_id","received_by_id","is_active","is_verified","type"]:param.pop(item,None)
   #logic
   key=""
   for k,v in param.items():key=key+f"{k}=coalesce(:{k},{k}) ,"
   query=f"update {table} set {key.strip().rsplit(',', 1)[0]} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   response=await function_query_runner(request.state.postgres_object,"write",query,param|{"id":id,"created_by_id":created_by_id})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.delete("/{x}/object-delete/{table}/{id}")
async def function_object_delete(request:Request,table:str,id:int,background_tasks:BackgroundTasks):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #refresh request_user
   response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   request_user=response["message"][0]
   #table check
   if table in ["users"]:return function_http_response(400,0,"table not allowed")
   #read object
   response=await function_query_runner(request.state.postgres_object,"read",f"select * from {table} where id={id};",{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no such object")
   object=response["message"][0]
   #permission check
   id,created_by_id=id,None
   if request_user["type"] not in ["root"]:
      if table=="users":id,created_by_id=request_user['id'],None
      else:id,created_by_id=id,request_user['id']
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   response=await function_query_runner(request.state.postgres_object,"write",query,{"id":id,"created_by_id":created_by_id})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #background task
   for item in ["likes","bookmark","comment","rating","block","report"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where parent_table=:parent_table and parent_id=:parent_id;",{"parent_table":table,"parent_id":id})
   if "file_url" in object:background_tasks.add_task(function_s3_delete_url,env.list("aws")[0],env.list("aws")[1],env.list("s3")[0],object["file_url"])
   #final response
   return {"status":1,"message":"object deleted"}

@router.get("/{x}/object-read-self/{table}/{page}")
async def function_object_read_self(request:Request,table:str,page:int,id:int=None,mode:str=None,limit:int=30):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #table=users
   if table=="users":
      response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"no user for token passed")
      return {"status":1,"message":response["message"][0]}
   #table!=users
   query,values=f"select * from {table} where (created_by_id=:created_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"created_by_id":request_user['id'],"id":id}
   if mode=="receiver":query,values=f"select * from {table} where (received_by_id=:received_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"received_by_id":request_user['id'],"id":id}
   if mode=="all":query,values=f"select * from {table} where (created_by_id=:created_by_id or received_by_id=:received_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"created_by_id":request_user['id'],"received_by_id":request_user['id'],"id":id}
   response=await function_query_runner(request.state.postgres_object,"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add count key
   if table in ["post"]:
      response=await function_add_like_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      response=await function_add_comment_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/object-read-public/{table}/{page}")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_object_read_public(request:Request,table:Literal["users","atom","post","comment","workseeker"],page:int,limit:int=30):
   #logic
   response=await function_object_read(request.state.postgres_object,function_query_runner,table,dict(request.query_params),["id","desc"],limit,(page-1)*limit,schema_atom)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add count key
   if table in ["post"]:
      response=await function_add_like_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      response=await function_add_comment_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/object-read-admin/{table}/{page}")
async def function_object_read_admin(request:Request,table:str,page:int,limit:int=30):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
   #logic
   response=await function_object_read(request.state.postgres_object,function_query_runner,table,dict(request.query_params),["id","desc"],limit,(page-1)*limit,schema_atom)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/pcache")
@cache(expire=60)
async def function_pcache(request:Request):    
    #logic
    output={}
    output["mapping_post_type"]={"funding123":"startup idea"}
    output["switch"]={"listing":0}
    output["admin_type"]=["root","admin"]
    #post type tag
    output["post_tag_type"]={}
    response=await function_query_runner(request.state.postgres_object,"read","select distinct(type) from post where type is not null;",{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    type_list=[item["type"] for item in response["message"] if item["type"]]
    for item in type_list:
        response=await function_query_runner(request.state.postgres_object,"read",f"with x as (select unnest(tag) as tag from post where type='{item}' and tag is not null) select tag,count(*) from x group by tag order by count desc limit 1000;",{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        output["post_tag_type"][item]=response["message"]
    #query
    query_dict={
    "post_tag":"with x as (select unnest(tag) as tag from post where tag is not null) select tag,count(*) from x group by tag order by count desc;",
    "user_tag":"with x as (select unnest(tag) as tag from users where tag is not null) select tag,count(*) from x group by tag order by count desc;",
    "user_count":"select count(*) from users;",
    "logo":"select * from atom where type='logo' and is_active=1 limit 1;",
    "about":"select * from atom where type='about' and is_active=1 limit 1;",
    "post_tag_trending":"select * from atom where type='post_tag_trending' and is_active=1 limit 1;",
    "curated":"select * from atom where type='curated' and is_active=1 order by id asc limit 1000;",
    "link":"select * from atom where type='link' and is_active=1 order by id asc limit 10;",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(request.state.postgres_object,"read",v,{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        output[k]=response["message"]
    #final response
    return {"status":1,"message":output}

@router.post("/{x}/insert-csv")
async def function_insert_csv(request:Request,table:str,file:UploadFile):
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root user allowed")
    if file.content_type!="text/csv":return function_http_response(400,0,"only csv allowed")
    if file.size>=100000:return function_http_response(400,0,"file size should be<=100000 bytes")
    file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
    if set(file_object.fieldnames)!=set(["created_by_id","type","title","description","file_url","link_url","tag"]):return function_http_response(400,0,"column mismatch")
    count=0
    for row in file_object:
        row["created_by_id"],row["tag"]=int(row["created_by_id"]) if row["created_by_id"] else None,row["tag"].split(",") if row["tag"] else None
        response=await function_query_runner(request.state.postgres_object,"write",f"insert into {table} (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;",row)
        if response["status"]==0:return function_http_response(400,0,response["message"])
        count+=1
    file.file.close
    return response

@router.put("/{x}/update-cell")
async def function_update_cell(request:Request,table:str,id:int,column:str,value:str):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #conversion
    response=await function_query_runner(request.state.postgres_object,"read","select data_type from information_schema.columns where column_name=:column_name limit 1;",{"column_name":column})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return {"status":0,"message":"no such column"}
    datatype=response["message"][0]["data_type"]
    if datatype in ["decimal","numeric","real","double precision"]:value=round(float(value),2)
    if datatype=="ARRAY":value=value.split(",")
    if datatype=="jsonb":value=json.dumps(value,default=str)
    if datatype=="integer":value=int(value)
    if datatype=="integer":value=int(value)
    if datatype=="timestamp with time zone":value=datetime.strptime(value,'%Y-%m-%d')
    if column in ["password","firebase_id","google_id"]:value=hashlib.sha256(value.encode()).hexdigest()
    #admin check
    id,created_by_id=id,None
    if request_user["type"] not in ["root","admin"]:
        if table=="users":id,created_by_id=request_user['id'],None
        else:id,created_by_id=id,request_user['id']
        if column in ["created_by_id","received_by_id","is_active","is_verified","type"]:return function_http_response(400,0,"column not allowed")
    #logic
    query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
    values={"value":value,"updated_at":datetime.now(),"updated_by_id":request_user['id'],"id":id,"created_by_id":created_by_id}
    response=await function_query_runner(request.state.postgres_object,"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return response
        
@router.get("/{x}/{function}")
async def function_function(request:Request,function:str,background_tasks:BackgroundTasks,filename:str=None,url:str=None,email:str=None,title:str=None,description:str=None,mode:str=None,query:str=None):
    #token check
    if function in ["create-s3-url","delete-s3-url","query-runner","token-refresh"]:
        response=await function_token_decode(request,env("key"))
        if response["status"]==0:return function_http_response(400,0,response["message"])
        request_user=response["message"]
    #logic
    if function=="create-s3-url":
        response=await function_create_s3_url(env.list("aws")[0],env.list("aws")[1],env.list("s3")[0],env.list("s3")[1],filename)
        if response["status"]==0:return function_http_response(400,0,response["message"])
        file_url=response["message"]['url']+response["message"]['fields']['key']
        background_tasks.add_task(function_query_runner,request.state.postgres_object,"write","insert into file (created_by_id,file_url) values (:created_by_id,:file_url) returning *;",{"created_by_id":request_user["id"],"file_url":file_url})
    if function=="delete-s3-url":
        if not url:return function_http_response(400,0,"url must")
        if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
        if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
        response=await function_s3_delete_url(env.list("aws")[0],env.list("aws")[1],env.list("s3")[0],url)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="send-email-ses":
        if any(not item for item in [email,title,description]):return function_http_response(400,0,"email/title/description must")
        response=await function_ses_send_email(env.list("aws")[0],env.list("aws")[1],env.list("ses")[0],env.list("ses")[1],email,title,description)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="send-otp-email":
        if not email:return function_http_response(400,0,"email must")
        otp=random.randint(100000,999999)
        response=await function_ses_send_email(env.list("aws")[0],env.list("aws")[1],env.list("ses")[0],env.list("ses")[1],email,"otp from atom",str(otp))
        if response["status"]==0:return function_http_response(400,0,response["message"])
        response=await function_query_runner(request.state.postgres_object,"write","insert into otp (created_by_id,otp,email) values (:created_by_id,:otp,:email) returning *;",{"created_by_id":None,"otp":otp,"email":email})
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="database-clean":
        response=await function_database_clean(request.state.postgres_object,function_query_runner)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="query-runner":
        if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root user allowed")
        response=await function_query_runner(request.state.postgres_object,mode,query,{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="token-refresh":
        response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        if not response["message"]:return function_http_response(400,0,"no user for token passed")
        user=response["message"][0]
        data=json.dumps({"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
        response=await function_token_encode(data,env("key"))
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="mongo":
        body=await request.json()
        if not mode:return function_http_response(400,0,"mode must")
        mongo_object=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
        if mode=="create":response=await mongo_object.test.users.insert_one(body)
        if mode=="read":response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
        if mode=="update":response=await mongo_object.test.users.update_one({"_id":ObjectId(body["id"])},{"$set":body})
        if mode=="delete":response=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
    if function=="elasticsearch":
        body=await request.json()
        if not mode:return function_http_response(400,0,"mode must")
        elasticsearch_object=Elasticsearch(cloud_id=cloud_id,basic_auth=(username,password))
        if mode=="create":response=elasticsearch_object.index(index="users",id=body["id"],document=body)
        if mode=="read":response=elasticsearch_object.get(index="users",id=body["id"])
        if mode=="update":response=elasticsearch_object.update(index="users",id=body["id"],doc=body)
        if mode=="delete":response=elasticsearch_object.delete(index="users",id=body["id"])
        if mode=="refresh":response=elasticsearch_object.indices.refresh(index="users")
        if mode=="search":response=elasticsearch_object.search(index="users",body={"query":{"match":{column:keyword}},"size":30})
    #final response
    return response
