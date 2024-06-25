#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from datetime import datetime
from fastapi_cache.decorator import cache
from fastapi import BackgroundTasks
import json
import uuid
import random

#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#api
@router.get("/{x}/pcache")
@cache(expire=60)
async def api_func(x:str,request:Request):
    #output
    output={}
    #custom
    output["admin_panel"]=config_admin_panel
    output["mapping_post_type"]={"hiring":"hiring post","funding":"funding post","workseeker":"looking for job","workgiver":"looking to hire","requirement":"requirement post"}
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
async def api_func(x:str,request:Request,table:str,id:int,column:str,value:str):
  #token check
  response=await function_token_decode(request,config_jwt_secret_key)
  if response["status"]==0:return function_http_response(400,0,response["message"])
  request_user=response["message"]
  #column not allowed
  if request_user["type"] not in ["root","admin"]:
      if column in ["created_by_id","received_by_id","is_active","is_verified","type"]:return function_http_response(400,0,"column not allowed")
  #validation
  if column=="username" and len(value)>100:return function_http_response(400,0,"value should be less than 100")
  if column=="password" and len(value)>1000:return function_http_response(400,0,"value should be less than 1000")
  if column=="username" and " " in value :return function_http_response(400,0,"username whitespace not allowed")
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
