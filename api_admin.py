#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from typing import Literal
from fastapi import File
from fastapi import UploadFile
import csv,codecs
from fastapi import BackgroundTasks

#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#api
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
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
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
   return {"status":1,"message":"done"}
   
@router.delete("/{x}/delete-s3-url")
async def function_api_delete_s3_url(x:str,request:Request,url:str,background_tasks:BackgroundTasks):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
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

@router.post("/{x}/insert-csv")
async def function_api_insert_csv(x:str,request:Request,table:Literal["atom","post"],file:UploadFile=File(...)):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root admin allowed")
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

@router.get("/{x}/query-runner")
async def function_api_query_runner(x:str,request:Request,mode:str,query:str):
   #token check
   response=await function_token_decode(request,config_jwt_secret_key)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root"]:return function_http_response(400,0,"only root admin allowed")
   #query alias
   if query=="database":query="select * from pg_database where datistemplate=false;"
   if query=="table":query="select * from information_schema.tables where table_schema='public' and table_type='BASE TABLE';"
   if query=="column":query="select * from information_schema.columns where table_schema='public';"
   if query=="constraint":query="select * from information_schema.constraint_column_usage;"
   if query=="index":query="select * from pg_indexes where schemaname='public';"
   if query=="column_count":query='''
   with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),
   y as (select table_name,count(*) as count_column from information_schema.columns group by table_name)
   select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;
   '''
   #logic
   response=await function_query_runner(postgres_object[x],mode,query,{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #finally
   return response
