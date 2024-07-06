#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal
import json
from fastapi import Body
from fastapi_cache.decorator import cache

#router
from fastapi import APIRouter
router=APIRouter(tags=["crud"])

#schema
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
class schema_atom(BaseModel):
   created_by_id:int|None=None
   received_by_id:int|None=None
   is_active:int|None=None
   is_verified:int|None=None
   parent_table:str|None=None
   parent_id:int|None=None
   username:str|None=None
   profile_pic_url:str|None=None
   name:str|None=None
   gender:str|None=None
   date_of_birth:datetime|None=None
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
   email:str|None=None
   mobile:str|None=None
   whatsapp:str|None=None
   phone:str|None=None
   country:str|None=None
   state:str|None=None
   city:str|None=None
   rating:int|None=None
   metadata:dict|None=None
   work_profile:str|None=None
   experience:int|None=None
   sector:str|None=None
   college:str|None=None
   linkedin_url:str|None=None
   portfolio_url:str|None=None
   location_current:str|None=None
   location_expected:str|None=None
   salary_type:str|None=None
   salary_current:int|None=None
   salary_expected:int|None=None
   past_company_count:int|None=None
   is_working:int|None=None
   joining_days:int|None=None

#api
@router.post("/{x}/object-create/{table}")
async def function_api_object_create(x:str,table:str,request:Request,body:schema_atom):
   #start
   request_user={}
   request_user["id"]=None
   #token check
   if request.headers.get("token") or table not in ["helpdesk","workseeker"]:
      response=await function_token_decode(request,config_jwt_secret_key)
      if response["status"]==0:return function_http_response(400,0,response["message"])
      request_user=response["message"]
   #param
   param=vars(body)
   param={k: v for k, v in param.items() if v is not None}
   if not param:return function_http_response(400,0,"all keys cant be null")
   #param validation
   response=await function_check_body(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #param conversion
   try:
      if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
      if "tag" in param:param["tag"]=list(dict.fromkeys(param["tag"]))
      if "tag" in param:param["tag"]=[x.strip(' ').lower() for x in param["tag"]]
      if "tag" in param:param["tag"]=[x[1:] if x[0]=="#" else x for x in param["tag"]]
      if "number" in param:param["number"]=round(param["number"],5)
   except Exception as e:return function_http_response(400,0,e.args)
   #param default
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
   #param
   param=vars(body)
   param={k: v for k, v in param.items() if v is not None}
   if not param:return function_http_response(400,0,"body null issue")
   #param validation
   response=await function_check_body(vars(body))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #param conversion
   try:
      if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
      if "tag" in param:param["tag"]=list(dict.fromkeys(param["tag"]))
      if "tag" in param:param["tag"]=[x.strip(' ').lower() for x in param["tag"]]
      if "tag" in param:param["tag"]=[x[1:] if x[0]=="#" else x for x in param["tag"]]
      if "number" in param:param["number"]=round(param["number"],5)
   except Exception as e:return function_http_response(400,0,e.args)
   #param keys not allowed
   if request_user["type"] not in ["root","admin"]:
      for item in ["created_by_id","received_by_id","is_active","is_verified","type"]:
         if item in param:del param[item]
   if not param:return function_http_response(400,0,"body null issue after not allowed keys remove")
   #permission set
   if request_user["type"] in ["root","admin"]:created_by_id=None
   else:
      if table=="users":created_by_id,id=None,request_user['id']
      if table!="users":created_by_id=request_user['id']
   #param default
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
async def function_api_object_read_public(x:str,request:Request,table:Literal["users","atom","post","comment","workseeker"],page:int,id:int=None,created_by_id:int=None,type:str=None,username:str=None,parent_table:str=None,parent_id:int=None,tag:str=None):
   #logic
   limit=30
   offset=(page-1)*limit
   if tag:tag=tag.split(",")
   param={"id":id,"created_by_id":created_by_id,"type":type,"username":username,"parent_table":parent_table,"parent_id":parent_id,"tag":tag}
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
