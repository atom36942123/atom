#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal
import json
import random
from fastapi import File
from fastapi import UploadFile
from fastapi import Body
import csv,codecs
from fastapi_cache.decorator import cache

#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#api
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
