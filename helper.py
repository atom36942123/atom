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
import boto3,uuid

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

#function
from fastapi import Request,Response
def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
    return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
def function_http_response(status_code,status,message):
    return JSONResponse(status_code=status_code,content=jsonable_encoder({"status":status,"message":message}))

async def function_query_runner(postgres_object,mode,query,values):
    if mode not in ["read","write"]:return {"status":0,"message":"wrong mode"}
    try:
        if mode=="read":output=list(map(lambda x:dict(x),await postgres_object.fetch_all(query=query,values=values)))
        if mode=="write":output=await postgres_object.execute(query=query,values=values)
    except Exception as e:return {"status":0,"message":e.args}
    return {"status":1,"message":output}

async def function_object_read(postgres_object,function_query_runner,table,param,order,limit,offset,schema_atom):
   #param
   param={k:v for k,v in param.items() if v not in [None,""," "]}
   if "tag" in param and param["tag"]:param["tag"]=param["tag"].split(",")
   param_schema_atom={k:v for k,v in vars(schema_atom(**param)).items() if v not in [None,""," "]}
   #operator
   operator={}
   for k,v in param_schema_atom.items():
       operator_name=f"{k}_operator"
       if operator_name in param:operator[k]=param[operator_name]
   #where
   where="where "
   for k,v in param_schema_atom.items():
      if k in operator:where=where+f"({k} {operator[k]} :{k} or :{k} is null) and "
      elif k=="tag":where=where+f"({k} @> :{k} or :{k} is null) and "
      else:where=where+f"({k} = :{k} or :{k} is null) and "
   where=where.strip().rsplit('and',1)[0]
   if where=="where":where=""
   #logic
   query=f"select * from {table} {where} order by {order[0]} {order[1]} limit {limit} offset {offset};"
   response=await function_query_runner(postgres_object,"read",query,param_schema_atom)
   if response["status"]==0:return response
   #final response
   return response

async def function_add_user_key(postgres_object,function_query_runner,object_list,user_column):
   #check
   if not object_list:return {"status":1,"message":object_list}
   if user_column not in ["created_by_id","received_by_id"]:return {"status":0,"message":"wrong user_column"}
   #select users
   user_ids=list(set([item[user_column] for item in object_list if item[user_column]]))
   query=f"select * from users join unnest(array{user_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
   response=await function_query_runner(postgres_object,"read",query,{})
   if response["status"]==0:return response
   object_list_user=response["message"]
   #set extra key
   for object in object_list:
      for user in object_list_user:
         if object[user_column]==user["id"]:
            if user_column=="created_by_id":
               object["created_by_username"],object["created_by_profile_pic_url"],object["created_by_type"]=user["username"],user["profile_pic_url"],user["type"]
            if user_column=="received_by_id":
               object["received_by_username"],object["received_by_profile_pic_url"],object["received_by_type"]=user["username"],user["profile_pic_url"],user["type"]
   #final response
   return {"status":1,"message":object_list}

async def function_add_like_count(postgres_object,function_query_runner,table,object_list):
   #check
   if not object_list:return {"status":1,"message":object_list}
   #fetch count
   ids=list(set([item["id"] for item in object_list if item["id"]]))
   query=f"select parent_id,count(*) from likes join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;"
   response=await function_query_runner(postgres_object,"read",query,{})
   if response["status"]==0:return response
   object_like_list=response["message"]
   #set count
   for object in object_list:
      object["like_count"]=0
      for object_like in object_like_list:
         if object["id"]==object_like["parent_id"]:object["like_count"]=object_like["count"]
   #final response
   return {"status":1,"message":object_list}

async def function_add_comment_count(postgres_object,function_query_runner,table,object_list):
   #check
   if not object_list:return {"status":1,"message":object_list}
   #fetch count
   ids=list(set([item["id"] for item in object_list if item["id"]]))
   query=f"select parent_id,count(*) from comment join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;"
   response=await function_query_runner(postgres_object,"read",query,{})
   if response["status"]==0:return response
   object_comment_list=response["message"]
   #set count
   for object in object_list:
      object["comment_count"]=0
      for object_comment in object_comment_list:
         if object["id"]==object_comment["parent_id"]:object["comment_count"]=object_comment["count"]
   #final response
   return {"status":1,"message":object_list}

import jwt,time
from datetime import datetime,timedelta
async def function_token_encode(data,secret_key):
   payload={"data":data}|{"exp":time.mktime((datetime.now()+timedelta(days=int(36500))).timetuple())}
   try:token=jwt.encode(payload,secret_key)
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":token}

import jwt,json
async def function_token_decode(request,secret_key):
   if not request.headers.get("token"):return {"status":0,"message":"token missing"}
   try:payload=jwt.decode(request.headers.get("token"),secret_key,algorithms="HS256")
   except Exception as e:return {"status":0,"message":e.args}
   data=json.loads(payload["data"])
   if "x" not in data or data["x"]!=str(request.url).split("/")[3]:return {"status":0,"message":"x encoded in token mismatch"}
   return {"status":1,"message":data}

import boto3
async def function_s3_delete_url(access_key_id,secret_access_key,bucket_name,url):
   if not url:return {"status":1,"message":"url null"}
   key_list=[item.split("/")[-1] for item in url.split(",") if bucket_name in item]
   try:output=list(map(lambda x:boto3.resource("s3",aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key).Object(bucket_name,x).delete(),key_list))
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":output}

import boto3
async def function_ses_send_email(access_key_id,secret_access_key,ses_sender,ses_region,to,title,description):
   try:output=boto3.client("ses",region_name=ses_region,aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key).send_email(Source=ses_sender,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":output}

async def function_update_mat_all(postgres_object,function_query_runner):
   #logic
   read_mat_all="select string_agg(oid::regclass::text,', ') as output from pg_class where relkind='m';"
   response=await function_query_runner(postgres_object,"read",read_mat_all,{})
   if response["status"]==0:return response
   mat_all_list=response["message"][0]["output"].split(",")
   for item in mat_all_list:
      query=f"refresh materialized view {item};"
      response=await function_query_runner(postgres_object,"write",query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_mat(postgres_object,function_query_runner):
   #logic
   drop_all_mat_get_query="select 'drop materialized view ' || string_agg(oid::regclass::text, ', ') || ' cascade;' as output from pg_class where relkind='m';"
   response=await function_query_runner(postgres_object,"read",drop_all_mat_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_index(postgres_object,function_query_runner):
   #logic
   drop_all_index_get_query='''
   select 'drop index ' || string_agg(i.indexrelid::regclass::text, ', ' order by n.nspname, 
   i.indrelid::regclass::text, cl.relname) as output
   from pg_index i
   join pg_class cl ON cl.oid = i.indexrelid
   join   pg_namespace n ON n.oid = cl.relnamespace
   left join pg_constraint co ON co.conindid = i.indexrelid
   where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null
   and not i.indisprimary and not i.indisunique and not i.indisexclusion 
   and not i.indisclustered and not i.indisreplident;
   '''
   response=await function_query_runner(postgres_object,"read",drop_all_index_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_view(postgres_object,function_query_runner):
   drop_all_view_get_query='''select 'drop view if exists ' || string_agg (table_name, ', ') || ' cascade;' as output from information_schema.views where table_schema not in ('pg_catalog', 'information_schema') and table_name !~ '^pg_';'''
   response=await function_query_runner(postgres_object,"read",drop_all_view_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   return {"status":1,"message":"done"}

async def function_database_clean(postgres_object,function_query_runner):
   #logic
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
      response=await function_query_runner(postgres_object,"write",v,{})
      if response["status"]==0:return response
   return {"status":1,"message":"done"}
