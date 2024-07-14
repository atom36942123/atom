#import
from config import *
from database import *
from schema import *
from function import *
from object import postgres_object
from fastapi import Request,Depends,Body,File,UploadFile
from fastapi import BackgroundTasks
from fastapi_limiter.depends import RateLimiter
from fastapi_cache.decorator import cache
from typing import Literal
from datetime import datetime
import hashlib,json,uuid,random,csv,codecs

#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#root
@router.get("/")
async def function_api_root():
   return {"status":1,"message":"welcome to atom"}

#database
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
        for table in v[0]:
            query=f"alter table {table} add column if not exists {k} {v[1]};"
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
    #default
    for k,v in config_column.items():
        for column in schema_column:
            for table in v[0]:
                if column["table_name"]==table and column["column_name"]==k and not column["column_default"] and v[1]:
                    query=f"alter table {table} alter column {k} set default {v[1]};"
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
    #final response
    return {"status":1,"message":"database init done"}

@router.get("/{x}/database-index")
async def function_api_database_index(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #drop all index
    response=await function_drop_all_index(postgres_object[x],function_query_runner)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #create index
    for k,v in config_column_index.items():
        for table in v[1]:
            index_name=f"index_{k.replace(',','_')}_{table}"
            query=f"create index if not exists {index_name} on {table}({k});"
            if v[0]=="array":query=f"create index if not exists {index_name} on {table} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"database index done"}

@router.get("/{x}/database-query")
async def function_api_database_query(x:str,request:Request):
    #token check
    if request.headers.get("token")!=config_token_root:return function_http_response(400,0,"token mismatch")
    #query define
    query_create_root_user="insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;"
    query_rule_delete_disable_users_root="create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;"
    query_index_likes"create index if not exists index_parent_table_parent_id_likes on likes(parent_table,parent_id);"
    query_index_bookmark"create index if not exists index_parent_table_parent_id_bookmark on bookmark(parent_table,parent_id);"
    query_index_comment"create index if not exists index_parent_table_parent_id_comment on comment(parent_table,parent_id);"
    #query run
    for item in [query_create_root_user,query_rule_delete_disable_users_root]:
        response=await function_query_runner(postgres_object[x],"write",item,{})
        if response["status"]==0:return function_http_response(400,0,f"error={response['message']}")
    #finally
    return {"status":1,"message":"database query done"}
    
#signup
@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_api_signup(x:str,request:Request,body:schema_signup):
   #param validaton
   response=await function_param_validation(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #read user
   query="select * from users where username=:username;"
   values={"username":body.username}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #check username if exist
   if response["message"]:return function_http_response(400,0,"username already exist")
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.post("/{x}/login")
async def function_api_login(x:str,request:Request,body:schema_login):
   #param validation
   response=await function_param_validation(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #username
   if body.mode=="username":
      #check body must
      if not body.username or not body.password:return function_http_response(400,0,"username/password must")
      #read user
      query="select * from users where username=:username and password=:password;"
      values={"username":body.username,"password":hashlib.sha256(body.password.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check user if not exist
      if not response["message"]:return function_http_response(400,0,"no such user")
      #user define
      user=response["message"][0]
   #firebase
   if body.mode=="firebase":
      #check body must
      if not body.firebase:return function_http_response(400,0,"firebase_id must")
      #read user
      query="select * from users where firebase_id=:firebase_id order by id desc limit 1;"
      values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (firebase_id) values (:firebase_id) returning *;"
         values={"firebase_id":hashlib.sha256(body.firebase_id.encode()).hexdigest()}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #email
   if body.mode=="email":
      #check body must
      if not body.email or not body.otp:return function_http_response(400,0,"email is must")
      #read otp
      query="select * from otp where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check if otp exist
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      #verify otp
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body.email}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (email) values (:email) returning *;"
         values={"email":body.email}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #mobile
   if body.mode=="mobile":
      #check body must
      if not body.mobile or not body.otp:return function_http_response(400,0,"mobile is must")
      #read otp
      query="select * from otp where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #check if otp exist
      if not response["message"]:return function_http_response(400,0,"otp not exist")
      #verify otp
      if response["message"][0]["otp"]!=body.otp:return function_http_response(400,0,"otp mismatched")
      #read user
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body.mobile}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      #user define
      if response["message"]:user=response["message"][0]
      #user define if not exist
      else:
         #user create
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body.mobile}
         response=await function_query_runner(postgres_object[x],"write",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #read user
         query="select * from users where id=:id;"
         values={"id":response["message"]}
         response=await function_query_runner(postgres_object[x],"read",query,values)
         if response["status"]==0:return function_http_response(400,0,response["message"])
         #user define
         user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/token-refresh")
async def function_api_token_refresh(x:str,request:Request):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #read user
   query="select * from users where id=:id;"
   values={"id":request_user["id"]}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #if user not exist
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   #user define
   user=response["message"][0]
   #token encode
   data={"x":x,"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   response=await function_token_encode(data,config_jwt_expire_day,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

#my
@router.get("/{x}/my-profile")
async def function_api_my_profile(x:str,request:Request,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #read user
    query="select * from users where id=:id;"
    values={"id":request_user["id"]}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #if user not exist
    if not response["message"]:return function_http_response(400,0,"no user exist for token passed")
    #background task (last active set)
    query=f"update users set last_active_at=:last_active_at where id=:id;"
    values={"last_active_at":datetime.now(),"id":response["message"][0]["id"]}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return {"status":1,"message":response["message"][0]}

@router.get("/{x}/my-profile-misc")
async def function_api_my_profile_misc(x:str,request:Request):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #output
    user={}
    #count key
    query_dict={
    "post_count":f"select count(*) as number from post where created_by_id={request_user['id']};",
    "comment_count":f"select count(*) as number from comment where created_by_id={request_user['id']};",
    "message_unread_count":f"select count(*) as number from message where received_by_id={request_user['id']} and status='unread';",
    "like_post_count":f"select count(*) as number from likes where created_by_id={request_user['id']} and parent_table='post';",
    "bookmark_post_count":f"select count(*) as number from bookmark where created_by_id={request_user['id']} and parent_table='post';",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(postgres_object[x],"read",v,{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        user[k]=response["message"][0]["number"]
    #finally
    return {"status":1,"message":user}
    
@router.get("/{x}/my-action-check")
async def function_api_my_action_check(x:str,request:Request,action:str,table:str,ids:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #if ids null
    if not ids:return function_http_response(400,0,f"dont call action check api if feed null")
    #ids split
    try:ids=[int(x) for x in ids.split(',')]
    except Exception as e:return function_http_response(400,0,e.args)
    #logic
    query=f"select parent_id from {action} join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
    values={"parent_table":table,"created_by_id":request_user["id"]}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #parent ids join
    try:ids_filtered=list(set([item["parent_id"] for item in response["message"] if item["parent_id"]]))
    except Exception as e:return function_http_response(400,0,e.args)
    #finally
    return {"status":1,"message":ids_filtered}

@router.get("/{x}/my-read-parent/{table}/{parent_table}/{page}")
async def function_api_my_read_parent(x:str,request:Request,table:str,parent_table:str,page:int):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #read parent ids
    limit=30
    offset=(page-1)*limit
    query=f"select parent_id from {table} where created_by_id=:created_by_id and parent_table=:parent_table order by id desc offset {offset} limit {limit};"
    values={"created_by_id":request_user["id"],"parent_table":parent_table}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    parent_ids=[x["parent_id"] for x in response["message"]]
     #read parent ids objects
    query=f"select * from {parent_table} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add like count
    response=await function_add_like_count(postgres_object[x],function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add comment count
    response=await function_add_comment_count(postgres_object[x],function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

@router.get("/{x}/my-message-inbox/{page}")
async def function_api_my_message_inbox(x:str,request:Request,page:int,is_unread:int=None):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #pagination set
    limit=30
    offset=(page-1)*limit
    #query set default
    query='''
    with
    mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),
    x as (select owner_id,max(id) as id from mcr group by owner_id offset :offset limit :limit),
    y as (select m.* from x left join message as m on x.id=m.id)
    select * from y order by id desc;
    '''
    values={"created_by_id":request_user['id'],"received_by_id":request_user['id'],"offset":offset,"limit":limit}
    #query set is unread
    if is_unread==1:
        query='''
        with
        mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),
        x as (select owner_id,max(id) as id from mcr group by owner_id),
        y as (select m.* from x left join message as m on x.id=m.id)
        select * from y where received_by_id=:received_by_id and status='unread' order by id desc offset :offset limit :limit;
        '''
        values={"created_by_id":request_user['id'],"received_by_id":request_user['id'],"offset":offset,"limit":limit}
    #query run
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"received_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

@router.get("/{x}/my-message-thread/{user_id}/{page}")
async def function_api_my_message_thread(x:str,request:Request,user_id:int,page:int,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    limit=30
    offset=(page-1)*limit
    query=f"select * from message where (created_by_id=:user_1 and received_by_id=:user_2) or (created_by_id=:user_2 and received_by_id=:user_1) order by id desc offset {offset} limit {limit}"
    values={"user_1":request_user["id"],"user_2":user_id}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"received_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #background task (set message status read)
    query=f"update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where received_by_id=:received_by_id and created_by_id=:created_by_id returning *;"
    values={"status":"read","updated_by_id":request_user['id'],"updated_at":datetime.now(),"received_by_id":request_user['id'],"created_by_id":user_id}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.delete("/{x}/my-delete")
async def function_api_my_delete(request:Request,x:str,mode:Literal["post_all","comment_all","message_all","like_post_all","bookmark_post_all","message_mutual","message_thread","like_post","bookmark_post"],user_id:int=None,post_id:int=None,message_id:int=None):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #query set
    if mode=="post_all":
        if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"user type not allowed")
        query="delete from post where created_by_id=:created_by_id;"
        values={"created_by_id":request_user['id']}
    if mode=="comment_all":
        query="delete from comment where created_by_id=:created_by_id;"
        values={"created_by_id":request_user['id']}
    if mode=="message_all":
        query="delete from message where created_by_id=:created_by_id or received_by_id=:received_by_id;"
        values={"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="like_post_all":
        query="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table;"
        values={"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="bookmark_post_all":
        query="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table;"
        values={"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="message_mutual":
        if not message_id:return function_http_response(400,0,"message_id must")
        query=f"delete from message where id=:id and (created_by_id=:created_by_id or received_by_id=:received_by_id);"
        values={"id":message_id,"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="message_thread":
        if not user_id:return function_http_response(400,0,"user_id must")
        query="delete from message where (created_by_id=:a and received_by_id=:b) or (created_by_id=:b and received_by_id=:a);"
        values={"a":request_user['id'],"b":user_id}   
    if mode=="like_post":
        if not post_id:return function_http_response(400,0,"post_id must")
        query="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;"
        values={"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    if mode=="bookmark_post":
        if not post_id:return function_http_response(400,0,"post_id must")
        query="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;"
        values={"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    #query run
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return {"status":1,"message":"object deleted"}

@router.delete("/{x}/my-delete-account")
async def function_api_my_delete_account(x:str,request:Request,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #permission check
    if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"admin user cant be deleted")
    #logic
    query="delete from users where id=:id;"
    values={"id":request_user["id"]}
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #delete abandon object
    query_dict={
    "post":f"delete from post where created_by_id={request_user['id']};",
    "likes":f"delete from likes where created_by_id={request_user['id']};",
    "bookmark":f"delete from bookmark where created_by_id={request_user['id']};",
    "report":f"delete from report where created_by_id={request_user['id']};",
    "rating":f"delete from rating where created_by_id={request_user['id']};",
    "message":f"delete from message where created_by_id={request_user['id']} or received_by_id={request_user['id']};",
    "rating_parent":f"delete from rating where parent_table='users' and parent_id={request_user['id']};",
    "report_parent":f"delete from report where parent_table='users' and parent_id={request_user['id']};",
    }
    for k,v in query_dict.items():background_tasks.add_task(function_query_runner,postgres_object[x],"write",v,{})
    #finally
    return {"status":1,"message":"done"}

#crud
@router.post("/{x}/object-create/{table}")
async def function_api_object_create(x:str,table:str,request:Request,body:schema_atom):
   #variable define
   request_user={}
   request_user["id"]=None
   #token check
   if request.headers.get("token") or table not in ["helpdesk","workseeker"]:
      response=await function_token_decode(request,config_jwt_secret_key)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      request_user=response["message"]
   #param define
   param=vars(body)
   param={k: v for k, v in param.items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"all body keys cant be null")
   #param validation
   response=await function_param_validation(param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #param table validation
   if table=="atom" and "type" not in param:return function_http_response(400,0,"type is must")
   if table=="comment" and "description" not in param:return function_http_response(400,0,"description is must")
   if table=="message" and "description" not in param:return function_http_response(400,0,"description is must")
   if table=="helpdesk" and "description" not in param:return function_http_response(400,0,"description is must")
   if table=="rating" and "rating" not in param:return function_http_response(400,0,"rating is must")
   #param conversion
   response=await function_param_conversion(param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   param=response["message"]
   #param key default set
   param["created_by_id"]=request_user["id"]
   if table in ["message"]:param["status"]="unread"
   #query key set
   try:
      key_1=",".join([*param])
      key_2=",".join([":"+item for item in [*param]])
   except Exception as e:return function_http_response(400,0,e.args)
   #logic
   query=f'''insert into {table} ({key_1}) values ({key_2}) returning *;'''
   response=await function_query_runner(postgres_object[x],"write",query,param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.put("/{x}/object-update/{table}/{id}")
async def function_api_object_update(x:str,request:Request,table:str,id:int,body:schema_atom):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #param define
   param=vars(body)
   param={k: v for k, v in param.items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"body null issue")
   #param validation
   response=await function_param_validation(param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #param conversion
   response=await function_param_conversion(param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   param=response["message"]
   #param key delete
   if request_user["type"] not in ["root","admin"]:
      for item in ["created_by_id","received_by_id","is_active","is_verified","type"]:
         if item in param:del param[item]
   if not param:return function_http_response(400,0,"body null issue after not allowed keys remove")
   #permission set
   if request_user["type"] in ["root","admin"]:created_by_id=None
   else:
      if table=="users":created_by_id,id=None,request_user['id']
      if table!="users":created_by_id=request_user['id']
   #param keys default set
   param["updated_at"]=datetime.now()
   param["updated_by_id"]=request_user["id"]
   #query key set
   try:
      key=""
      for k,v in param.items():key=key+f"{k}=coalesce(:{k},{k}) ,"
      key=key.strip().rsplit(',', 1)[0]
   except Exception as e:return function_http_response(400,0,e.args)
   #logic
   query=f"update {table} set {key} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   values=param|{"id":id,"created_by_id":created_by_id}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.delete("/{x}/object-delete/{table}/{id}")
async def function_api_object_delete(x:str,request:Request,table:str,id:int,background_tasks:BackgroundTasks):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #check table
   if table=="users":return function_http_response(400,0,"users table not allowed")
   #read object
   query=f"select * from {table} where id={id};"
   response=await function_query_runner(postgres_object[x],"read",query,{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no such object")
   object=response["message"][0]
   #permission set
   if request_user["type"] in ["root"]:created_by_id=None
   else:
      if table=="users":created_by_id,id=None,request_user['id']
      if table!="users":created_by_id=request_user['id']
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={"id":id,"created_by_id":created_by_id}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #delete post child
   if table in ["post"]:
      query_dict={
      "likes":f"delete from likes where parent_table='post' and parent_id={id};",
      "bookmark":f"delete from bookmark where parent_table='post' and parent_id={id};",
      "report":f"delete from report where parent_table='post' and parent_id={id};",
      "rating":f"delete from rating where parent_table='post' and parent_id={id};",
      "comment":f"delete from comment where parent_table='post' and parent_id={id};",
      }
      for k,v in query_dict.items():background_tasks.add_task(function_query_runner,postgres_object[x],"write",v,{})
   #delete s3
   if "file_url" in object and object["file_url"]:
      for url in object["file_url"].split(","):
         if config_aws_s3_bucket_name in url:
            background_tasks.add_task(function_s3_delete_url,config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,url)
   #finally
   return {"status":1,"message":"object deleted"}

@router.get("/{x}/object-read-self/{table}/{page}")
async def function_api_object_read_self(x:str,request:Request,table:str,page:int,id:int=None):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #table=users
   if table=="users":
      query="select * from users where id=:id;"
      values={"id":request_user["id"]}
      response=await function_query_runner(postgres_object[x],"read",query,values)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"no user for token passed")
      user=response["message"][0]
      return {"status":1,"message":user}
   #table!=users
   limit=30
   offset=(page-1)*limit
   query=f"select * from {table} where (created_by_id=:created_by_id) and (id=:id or :id is null) order by id desc offset {offset} limit {limit};"
   values={"created_by_id":request_user['id'],"id":id}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   if table in ["post","comment"]:
      response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"created_by_id")
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #add like count
   if table in ["post"]:
      response=await function_add_like_count(postgres_object[x],function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #add comment count
   if table in ["post"]:
      response=await function_add_comment_count(postgres_object[x],function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/object-read-public/{table}/{page}")
@cache(expire=60)
async def function_api_object_read_public(x:str,request:Request,table:Literal["users","atom","post","comment","workseeker"],page:int,id:int=None,created_by_id:int=None,type:str=None,username:str=None,parent_table:str=None,parent_id:int=None,tag:str=None,is_pinned:int=None):
   #logic
   limit=30
   offset=(page-1)*limit
   if tag:tag=tag.split(",")
   param={"id":id,"created_by_id":created_by_id,"type":type,"username":username,"parent_table":parent_table,"parent_id":parent_id,"tag":tag,"is_pinned":is_pinned}
   response=await function_object_read(postgres_object[x],function_query_runner,table,param,["id","desc"],limit,offset)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   if table in ["post","comment"]:
      response=await function_add_user_key(postgres_object[x],function_query_runner,response["message"],"created_by_id")
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #add like count
   if table in ["post"]:
      response=await function_add_like_count(postgres_object[x],function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #add comment count
   if table in ["post"]:
      response=await function_add_comment_count(postgres_object[x],function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/object-read-admin/{table}/{page}")
async def function_api_object_read_admin(x:str,request:Request,table:str,page:int,id:int=None,created_by_id:int=None,type:str=None,username:str=None,parent_table:str=None,parent_id:int=None,tag:str=None):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
   #logic
   limit=30
   offset=(page-1)*limit
   if tag:tag=tag.split(",")
   param={"id":id,"created_by_id":created_by_id,"type":type,"username":username,"parent_table":parent_table,"parent_id":parent_id,"tag":tag}
   response=await function_object_read(postgres_object[x],function_query_runner,table,param,["id","desc"],limit,offset)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

#utility
@router.get("/{x}/pcache")
@cache(expire=60)
async def function_api_pcache(x:str,request:Request):
    #output define
    output={}
    #custom
    output["mapping_post_type"]={"funding123":"startup idea"}
    output["switch"]={"listing":0}
    output["admin_type"]=["root","admin"]
    #post type tag
    output["post_tag_type"]={}
    query="select distinct(type) from post where type is not null;"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    type_list=[item["type"] for item in response["message"] if item["type"]]
    for item in type_list:
        query=f"with x as (select unnest(tag) as tag from post where type='{item}' and tag is not null) select tag,count(*) from x group by tag order by count desc limit 1000;"
        response=await function_query_runner(postgres_object[x],"read",query,{})
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
        response=await function_query_runner(postgres_object[x],"read",v,{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        output[k]=response["message"]
    #finally
    return {"status":1,"message":output}
    
@router.get("/{x}/create-s3-url")
async def function_api_create_s3_url(x:str,request:Request,filename:str,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #param validation
    if "." not in filename:return function_http_response(400,0,"file extenstion is must")
    #key generate
    key=str(uuid.uuid4())+"."+filename.split(".")[-1]
    #loggic
    response=await function_s3_create_url(config_aws_s3_bucket_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #background task (save s3 url)
    query="insert into s3 (created_by_id,file_url) values (:created_by_id,:file_url) returning *;"
    values={"created_by_id":request_user["id"],"file_url":response["message"]['url']+response["message"]['fields']['key']}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.get("/{x}/send-email")
async def function_api_send_email(x:str,request:Request,to:str,title:str,description:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #param validation
    param={"email":to,"title":title,"description":description}
    response=await function_param_validation(param)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #logic
    response=await function_ses_send_email(config_aws_ses_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_ses_sender,to,title,description)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

@router.get("/{x}/send-otp")
async def function_api_send_otp(x:str,request:Request,email:str=None,mobile:str=None):
    #param must check
    if not email and not mobile:return function_http_response(400,0,"email/mobile any one is must")
    #param validation
    param={"email":email,"mobile":mobile}
    response=await function_param_validation(param)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #generate otp
    otp=random.randint(100000,999999)
    #logic email
    if email:
        response=await function_ses_send_email(config_aws_ses_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_ses_sender,email,"otp from atom",str(otp))
        if response["status"]==0:return function_http_response(400,0,response["message"])
    #logic mobile
    #save otp
    query="insert into otp (created_by_id,otp,email,mobile) values (:created_by_id,:otp,:email,:mobile) returning *;"
    values={"created_by_id":None,"otp":otp,"email":email,"mobile":mobile}
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return {"status":1,"message":"opt sent"}

@router.put("/{x}/update-cell")
async def function_api_update_cell(x:str,request:Request,table:str,id:int,column:str,value:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #column not allowed based on permission
    if request_user["type"] not in ["root","admin"]:
        if column in ["created_by_id","received_by_id","is_active","is_verified","type"]:return function_http_response(400,0,"column not allowed")
    #param validation
    param={column:value}
    response=await function_param_validation(param)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #read datatype
    query="select data_type from information_schema.columns where column_name=:column_name limit 1;"
    values={"column_name":column}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return {"status":0,"message":"no such column"}
    column_datatype=response["message"][0]["data_type"]
    #conversion
    try:
        if column in ["password","firebase_id"]:value=hashlib.sha256(value.encode()).hexdigest()
        if column_datatype in ["decimal","numeric","real","double precision"]:value=round(float(value),2)
        if column_datatype=="ARRAY":value=value.split(",")
        if column_datatype=="jsonb":value=json.dumps(value,default=str)
        if column_datatype=="integer":value=int(value)
    except Exception as e:return function_http_response(400,0,e.args)
    #permission set
    if request_user["type"] in ["root","admin"]:created_by_id=None
    else:
        if table=="users":created_by_id,id=None,request_user['id']
        if table!="users":created_by_id=request_user['id']
    #logic
    query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
    values={"value":value,"updated_at":datetime.now(),"updated_by_id":request_user['id'],"id":id,"created_by_id":created_by_id}
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

#admin
@router.get("/{x}/checklist")
async def function_api_checklist(x:str,request:Request):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #read user
   query="select * from users where id=:id;"
   values={"id":request_user["id"]}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user exist for token passed")
   user=response["message"][0]
   #refresh request user
   request_user=user
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
   #root user check
   query="select * from users where id=1;"
   response=await function_query_runner(postgres_object[x],"read",query,{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"root user null issue")
   object=response["message"][0]
   if object["username"]!="root" or object["is_active"]!=1 or object["type"]!="root":return function_http_response(400,0,"root user data issue")
   #query
   query_dict={
   "delete_post_creator_null":"delete from post where id in (select x.id from post as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_likes_creator_null":"delete from likes where id in (select x.id from likes as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_bookmark_creator_null":"delete from bookmark where id in (select x.id from bookmark as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_report_creator_null":"delete from report where id in (select x.id from report as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_comment_creator_null":"delete from comment where id in (select x.id from comment as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_rating_creator_null":"delete from rating where id in (select x.id from rating as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_block_creator_null":"delete from block where id in (select x.id from block as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_likes_parent_null_post":"delete from likes where id in (select x.id from likes as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_bookmark_parent_null_post":"delete from bookmark where id in (select x.id from bookmark as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_comment_parent_null_post":"delete from comment where id in (select x.id from comment as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_duplicate_tag":"delete from atom as a1 using atom as a2 where a1.type='tag' and a2.type='tag' and a1.ctid>a2.ctid and a1.title=a2.title;",
   "delete_message_old":"delete from message where created_at<now()-interval '30 days';",
   }
   for k,v in query_dict.items():
      response=await function_query_runner(postgres_object[x],"write",v,{})
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return {"status":1,"message":"checklist done"}
   
@router.delete("/{x}/delete-s3-url")
async def function_api_delete_s3_url(x:str,request:Request,url:str,background_tasks:BackgroundTasks):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
   #param validation
   if config_aws_s3_bucket_name not in url:return function_http_response(400,0,"invalid url")
   #logic
   response=await function_s3_delete_url(config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,url)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #background task (delete saved url)
   query="delete from s3 where file_url=:file_url;"
   values={"file_url":url}
   background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
   #finally
   return response

@router.post("/{x}/insert-csv")
async def function_api_insert_csv(x:str,request:Request,table:Literal["atom","post"],file:UploadFile=File(...)):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root admin allowed")
   #param validation
   if file.content_type!="text/csv":return function_http_response(400,0,"only csv allowed")
   if file.size>=100000:return function_http_response(400,0,"file size should be<=100000 bytes")
   #file object
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   #column allowed check
   column_allowed=["created_by_id","type","title","description","file_url","link_url","tag"]
   csv_column=file_object.fieldnames
   if set(csv_column)!=set(column_allowed):return function_http_response(400,0,"column mismatch")
   #logic
   count=0
   query=f"insert into {table} (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;"
   for row in file_object:
      try:
         row["created_by_id"]=int(row["created_by_id"]) if row["created_by_id"] else None
         row["tag"]=row["tag"].split(",") if row["tag"] else None
      except Exception as e:return function_http_response(400,0,e.args)
      response=await function_query_runner(postgres_object[x],"write",query,row)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      count+=1
   file.file.close
   #finally
   return {"status":1,"message":f"rows inserted={count}"}

@router.get("/{x}/query-runner")
async def function_api_query_runner(x:str,request:Request,mode:str,query:str):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root admin allowed")
   #logic
   response=await function_query_runner(postgres_object[x],mode,query,{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response


    

