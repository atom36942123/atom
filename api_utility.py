#import
from object import postgres_object
from config import *
from function import *
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal
import json
import random
import uuid
from fastapi import File
from fastapi import UploadFile
from fastapi import Body
import csv,codecs
from fastapi_cache.decorator import cache

#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

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
    #column add
    mapping_column_add={
    "created_at":["timestamptz",config_table],
    "created_by_id":["bigint",config_table],
    "updated_at":["timestamptz",["atom","users","post","comment","report","message","helpdesk","workseeker"]],
    "updated_by_id":["bigint",["atom","users","post","comment","report","message","helpdesk","workseeker"]],
    "received_by_id":["bigint",["message"]],
    "is_active":["int",["atom","users","post","comment","workseeker"]],
    "is_verified":["int",["atom","users","post","comment","workseeker"]],
    "is_admin":["int",["atom","users","post"]],
    "is_deleted":["int",[]],
        
    "username":["text",["users"]],
    "password":["text",["users"]],
    "firebase_id":["text",["users"]],
    "last_active_at":["timestamptz",["users"]],
    "name":["text",["users","workseeker"]],
    "gender":["text",["users","workseeker"]],
    "date_of_birth":["date",["users"]],
    "profile_pic_url":["text",["users"]],
        
    "college":["text",["workseeker"]],
    "linkedin_url":["text",["workseeker"]],
    "portfolio_url":["text",["workseeker"]],
    "work_profile":["text",["workseeker"]],
    "experience":["int",["workseeker"]],
    "location_current":["text",["workseeker"]],
    "location_expected":["text",["workseeker"]],
    "salary_type":["text",["workseeker"]],
    "salary_current":["int",["workseeker"]],
    "salary_expected":["int",["workseeker"]],
    "sector":["text",["workseeker"]],
    "total_past_company":["int",["workseeker"]],
    "is_working":["int",["workseeker"]],
    "joining_days":["int",["workseeker"]],

    "type":["text",["atom","users","post","helpdesk","workseeker"]],
    "title":["text",["atom","users","post"]],
    "description":["text",["atom","users","post","comment","report","rating","block","message","helpdesk","workseeker"]],
    "file_url":["text",["atom","post","s3"]],
    "link_url":["text",["atom","post"]],
    "tag":["text[]",["atom","users","post","workseeker"]],
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
        
    "metadata":["jsonb",["post"]],
    "xxx":["text",["atom"]],
    }
    for k,v in mapping_column_add.items():
        for item in v[1]:
            query=f"alter table {item} add column if not exists {k} {v[0]};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_add_error={response['message']}+{query}")
    #column delete
    mapping_column_delete={
    "xxx":["atom"],
    }
    for k,v in mapping_column_delete.items():
        for item in v:
            query=f"alter table {item} drop column if exists {k};"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_index_error={response['message']}+{query}")
    #constraint list
    query="select constraint_name from information_schema.constraint_column_usage;"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    constraint_name_list=[item["constraint_name"] for item in response["message"]]
    #column info
    query="select * from information_schema.columns where table_schema='public';"
    response=await function_query_runner(postgres_object[x],"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    column_info=response["message"]
    #column default
    mapping_column_default={
    "created_at":["now()",config_table],
    "last_active_at":["now()",["users"]],
    "is_active":["1",["atom","users","post","comment"]],
    "is_verified":["0",["atom","users","post","comment"]],
    "is_admin":["0",["atom","users","post"]],
    }
    for k,v in mapping_column_default.items():
        for item in v[1]:
            for column in column_info:
                if column["table_name"]==item and column["column_name"]==k and not column["column_default"]:
                    query=f"alter table {item} alter column {k} set default {v[0]};"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"column_default_error={response['message']}+{query}")
    #column not null
    mapping_column_not_null={
    "created_by_id":["likes","comment","bookmark","report","rating","block","message"],
    "parent_table":["likes","comment","bookmark","report","rating","block"],
    "parent_id":["likes","comment","bookmark","report","rating","block"],
    "received_by_id":["message"],
    "is_active":["atom","users","post","comment"],
    "is_verified":["atom","users","post","comment"],
    "is_admin":["atom","users","post"],
    }
    for k,v in mapping_column_not_null.items():
        for item in v:
            for column in column_info:
                if column["table_name"]==item and column["column_name"]==k and column["is_nullable"]=="YES":
                    query=f"alter table {item} alter column {k} set not null;"
                    response=await function_query_runner(postgres_object[x],"write",query,{})
                    if response["status"]==0:return function_http_response(400,0,f"column_not_null_error={response['message']}+{query}")
    #column unique
    mapping_column_unique={
    "username":["users"],
    "created_by_id,parent_table,parent_id":["likes","bookmark","report","block"],
    }
    query=f"alter table {v[0]} add constraint {k} unique ({v[1]});"
    for k,v in mapping_column_unique.items():
        for item in v:
            constraint_name=f"unique_{k}_{item}".replace(",","_")
            if constraint_name not in constraint_name_list:
                query=f"alter table {item} add constraint {constraint_name} unique ({k});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"column_unique_error={response['message']}+{query}")
    #column check in
    mapping_column_check_in={
    "is_active":["(0,1)",["atom","users","post","comment"]],
    "is_verified":["(0,1)",["atom","users","post","comment"]],
    "is_admin":["(0,1)",["atom","users","post"]],
    }
    for k,v in mapping_column_check_in.items():
        for item in v[1]:
            constraint_name=f"check_in_{k}_{item}"
            if constraint_name not in constraint_name_list:
                query=f"alter table {item} add constraint {constraint_name} check ({k} in {v[0]});"
                response=await function_query_runner(postgres_object[x],"write",query,{})
                if response["status"]==0:return function_http_response(400,0,f"column_check_in_error={response['message']}+{query}")
    #column index
    mapping_column_index={
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
    for k,v in mapping_column_index.items():
        for item in v:
            query=f"create index if not exists index_{k}_{item} on {item}({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_index_error={response['message']}+{query}")
    #column index array
    mapping_column_index_array={
    "tag":["atom","users","post"],
    }
    for k,v in mapping_column_index_array.items():
        for item in v:
            query=f"create index if not exists index_{k}_{item} on {item} using gin ({k});"
            response=await function_query_runner(postgres_object[x],"write",query,{})
            if response["status"]==0:return function_http_response(400,0,f"column_index_array_error={response['message']}+{query}")
    #query
    query_dict={
    "rule_delete_disable_atom":"create or replace rule rule_delete_disable_atom as on delete to atom where old.is_admin=1 do instead nothing;",
    "rule_delete_disable_post":"create or replace rule rule_delete_disable_post as on delete to post where old.is_admin=1 do instead nothing;",
    "rule_delete_disable_users":"create or replace rule rule_delete_disable_users as on delete to users where old.is_admin=1 do instead nothing;",
    "rule_delete_disable_root":"create or replace rule rule_delete_disable_root as on delete to users where old.id=1 do instead nothing;",
    "index_comment_pp": "create index if not exists index_comment_pp on comment(parent_table,parent_id);",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(postgres_object[x],"write",v,{})
        if response["status"]==0:return function_http_response(400,0,f"query error={response['message']}")
    #create root user
    query="insert into users (username,password,is_admin) values (:username,:password,:is_admin) on conflict do nothing returning *;"
    values={"username":"root","password":"a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3","is_admin":1}
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,f"root_user_create_error={response['message']}+{query}")
    #finally
    return {"status":1,"message":"done"}

@router.get("/{x}/create-s3-url")
async def api_func(x:str,request:Request,filename:str,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    key=str(uuid.uuid4())+"."+filename.split(".")[-1]
    response=await function_s3_create_url(config_aws_s3_bucket_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #save s3 url
    query="insert into s3 (created_by_id,file_url) values (:created_by_id,:file_url) returning *;"
    values={"created_by_id":request_user["id"],"file_url":response["message"]['url']+response["message"]['fields']['key']}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.delete("/{x}/delete-s3-url")
async def api_func(x:str,request:Request,url:str,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #admin check
    if request_user["is_admin"]!=1:return function_http_response(400,0,"only admin allowed")
    if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
    #check
    if config_aws_s3_bucket_name not in url:return function_http_response(400,0,"invalid url")
    #logic
    response=await function_s3_delete_url(config_aws_access_key_id,config_aws_secret_access_key,config_aws_s3_bucket_name,url)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #delete saved url
    query="delete from s3 where file_url=:file_url;"
    values={"file_url":url}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.get("/{x}/send-email")
async def api_func(x:str,request:Request,to:str,title:str,description:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    response=await function_ses_send_email(config_aws_ses_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_ses_sender,to,title,description)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

@router.get("/{x}/send-otp")
async def api_func(x:str,request:Request,email:str=None,mobile:str=None):
   #check
   if not email and not mobile:return function_http_response(400,0,"email/mobile any one is must")
   #logic
   otp=random.randint(100000,999999)
   if email:
      response=await function_ses_send_email(config_aws_ses_region,config_aws_access_key_id,config_aws_secret_access_key,config_aws_ses_sender,email,"otp from atom",str(otp))
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #save otp
   query="insert into otp (created_by_id,otp,email,mobile) values (:created_by_id,:otp,:email,:mobile) returning *;"
   values={"created_by_id":None,"otp":otp,"email":email,"mobile":mobile}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/query-runner")
async def api_func(x:str,request:Request,mode:str,query:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #admin check
    if request_user["is_admin"]!=1:return function_http_response(400,0,"only admin allowed")
    if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
    #check keywords
    if request_user["id"]!=1:
        if "insert" in query:return function_http_response(400,0,"insert in query not allowed")
        if "delete" in query:return function_http_response(400,0,"delete in query not allowed")
        if "alter" in query:return function_http_response(400,0,"alter in query not allowed")
        if "select" not in query:return function_http_response(400,0,"select in query is must")
    #logic
    response=await function_query_runner(postgres_object[x],mode,query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return response

@router.post("/{x}/insert-csv")
async def api_func(x:str,request:Request,table:Literal["atom","post"],file:UploadFile=File(...)):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #refresh request_user
    param={"id":request_user["id"]}
    response=await function_object_read(postgres_object[x],function_query_runner,"users",param,["id","desc",1,0])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return function_http_response(400,0,"no user for token passed")
    request_user=response["message"][0]
    #admin check
    if request_user["is_admin"]!=1:return function_http_response(400,0,"only admin allowed")
    if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
    if request_user["id"]!=1:return function_http_response(400,0,"only root user allowed")
    #prework
    if file.content_type!="text/csv":return function_http_response(400,0,"only csv allowed")
    if file.size>=100000:return function_http_response(400,0,"file size should be<=100000 bytes")
    file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
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

@router.put("/{x}/update-cell")
async def api_func(x:str,request:Request,table:str,id:int,column:str,value:str):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #set self
   created_by_id=None
   if request_user["is_admin"]==0 and table=="users":id,created_by_id=request_user['id'],None
   if request_user["is_admin"]==0 and table!="users":created_by_id=request_user['id']
   #validation/conversion
   if column=="username" and len(value)>100:return function_http_response(400,0,"value should be less than 100")
   if column=="password" and len(value)>1000:return function_http_response(400,0,"value should be less than 1000")
   if column=="username" and " " in value :return function_http_response(400,0,"username whitespace not allowed")
   if column in ["password","firebase_id"]:value=hashlib.sha256(value.encode()).hexdigest()
   #datatype conversion
   query="select data_type from information_schema.columns where column_name=:column_name limit 1;"
   values={"column_name":column}
   response=await function_query_runner(postgres_object[x],"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return {"status":0,"message":"no such column"}
   column_datatype=response["message"][0]["data_type"]
   try:
       if column_datatype in ["smallint","integer","bigint","smallserial","serial","bigserial"]:value=int(value)
       if column_datatype in ["decimal","numeric","real","double precision"]:value=round(float(value),2)
       if column_datatype=="ARRAY":value=value.split(",")
       if column_datatype=="jsonb":value=json.dumps(value,default=str)
   except Exception as e:return function_http_response(400,0,e.args)
   #logic
   query=f"update {table} set {column}=:value,updated_by_id=:updated_by_id,updated_at=:updated_at where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   values={"value":value,"updated_at":datetime.now(),"updated_by_id":request_user['id'],"id":id,"created_by_id":created_by_id}
   response=await function_query_runner(postgres_object[x],"write",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response

@router.get("/{x}/checklist")
async def api_func(x:str,request:Request):
   #ops query
   query_dict={
   "post_creator_null":"delete from post where id in (select x.id from post as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "likes_creator_null":"delete from likes where id in (select x.id from likes as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "bookmark_creator_null":"delete from bookmark where id in (select x.id from bookmark as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "report_creator_null":"delete from report where id in (select x.id from report as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "comment_creator_null":"delete from comment where id in (select x.id from comment as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "rating_creator_null":"delete from rating where id in (select x.id from rating as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "block_creator_null":"delete from block where id in (select x.id from block as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "likes_parent_null_post":"delete from likes where id in (select x.id from likes as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "bookmark_parent_null_post":"delete from bookmark where id in (select x.id from bookmark as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "comment_parent_null_post":"delete from comment where id in (select x.id from comment as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "mark_post_admin":"update post set is_admin=1 where id in (select p.id from post as p left join users as u on p.created_by_id=u.id where p.is_admin=0 and u.is_admin=1);",
   "delete_duplicate_tag":"delete from atom as a1 using atom as a2 where a1.type='tag' and a2.type='tag' and a1.ctid>a2.ctid and a1.title=a2.title;",
   "delete_message_old":"delete from message where created_at<now()-interval '30 days';",
   }
   for k,v in query_dict.items():
      response=await function_query_runner(postgres_object[x],"write",v,{})
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #root user check
   query="select * from users where id=1;"
   response=await function_query_runner(postgres_object[x],"read",query,{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"root user null issue")
   object=response["message"][0]
   if object["username"]!="root" or object["is_admin"]!=1 or object["is_active"]!=1:return function_http_response(400,0,"root user data issue")
   #finally
   return {"status":1,"message":"done"}

@router.get("/{x}/pcache")
@cache(expire=60)
async def api_func(x:str,request:Request):
   #general-query
   output={}
   query_dict={
   "post_tag":"with x as (select unnest(tag) as tag from post where tag is not null) select tag,count(*) from x group by tag order by count desc;",
   "user_tag":"with x as (select unnest(tag) as tag from users where tag is not null) select tag,count(*) from x group by tag order by count desc;",
   "user_count":"select count(*) from users;",
   }
   for k,v in query_dict.items():
      response=await function_query_runner(postgres_object[x],"read",v,{})
      if response["status"]==0:return function_http_response(400,0,response["message"])
      output[k]=response["message"]
   #general-post type tag
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
   #custom-direct
   output["admin_panel"]=config_admin_panel
   output["mapping_post_type"]={"hiring":"hiring post","funding":"funding post","workseeker":"looking for job","workgiver":"looking to hire","requirement":"requirement post"}
   #custom-query
   query_dict={
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
