#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from typing import Literal
from fastapi import File
from fastapi import UploadFile
import csv,codecs

#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#api
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
