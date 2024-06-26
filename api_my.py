#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal

#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#api
@router.get("/{x}/my-profile")
async def api_func_my_profile(x:str,request:Request,background_tasks:BackgroundTasks):
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
    #background task
    query=f"update users set last_active_at=:last_active_at where id=:id;"
    values={"last_active_at":datetime.now(),"id":request_user['id']}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return {"status":1,"message":request_user}

@router.get("/{x}/my-metric")
async def api_func_my_metric(x:str,request:Request,mode:str=None):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #if mode
    if mode=="message_unread":
      query=f"select count(*) from message where received_by_id={request_user['id']} and status='unread';"
      response=await function_query_runner(postgres_object[x],"read",query,{})
      if response["status"]==0:return function_http_response(400,0,response["message"])
      return {"status":1,"message":response["message"][0]["count"]}
    #if moode null
    output={}
    query_dict={
    "post":f"select count(*) as number from post where created_by_id={request_user['id']};",
    "comment":f"select count(*) as number from comment where created_by_id={request_user['id']};",
    "bookmark_post":f"select count(*) as number from bookmark where parent_table='post' and created_by_id={request_user['id']};",
    "like_post":f"select count(*) as number from likes where parent_table='post' and created_by_id={request_user['id']};",
    "message_unread":f"select count(*) as number from message where received_by_id={request_user['id']} and status='unread';"
    }
    for k,v in query_dict.items():
      response=await function_query_runner(postgres_object[x],"read",v,{})
      if response["status"]==0:return function_http_response(400,0,response["message"])
      output[k]=response["message"][0]["number"]
    #finally
    return {"status":1,"message":output}

@router.get("/{x}/my-action-check")
async def api_func_my_action_check(x:str,request:Request,action:str,table:str,ids:str):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #check
    if not ids:return function_http_response(400,0,f"dont call action check api if feed null")
    #logic
    try:ids=[int(x) for x in ids.split(',')]
    except Exception as e:return function_http_response(400,0,e.args)
    query=f"select parent_id from {action} join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
    values={"parent_table":table,"created_by_id":request_user["id"]}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    try:ids_filtered=list(set([item["parent_id"] for item in response["message"] if item["parent_id"]]))
    except Exception as e:return function_http_response(400,0,e.args)
    #finally
    return {"status":1,"message":ids_filtered}

@router.get("/{x}/my-read-parent/{table}/{parent_table}/{page}")
async def api_func_my_read_parent(x:str,request:Request,table:str,parent_table:str,page:int):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #get parent ids
    limit=30
    offset=(page-1)*limit
    query=f"select parent_id from {table} where created_by_id=:created_by_id and parent_table=:parent_table order by id desc offset {offset} limit {limit};"
    values={"created_by_id":request_user["id"],"parent_table":parent_table}
    response=await function_query_runner(postgres_object[x],"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    parent_ids=[x["parent_id"] for x in response["message"]]
    #read parent ids
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
async def api_func_my_message_inbox(x:str,request:Request,page:int,is_unread:int=None):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    limit=30
    offset=(page-1)*limit
    query='''
    with
    mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),
    x as (select owner_id,max(id) as id from mcr group by owner_id offset :offset limit :limit),
    y as (select m.* from x left join message as m on x.id=m.id)
    select * from y order by id desc;
    '''
    values={"created_by_id":request_user['id'],"received_by_id":request_user['id'],"offset":offset,"limit":limit}
    if is_unread==1:
      query='''
      with
      mcr as (select id,created_by_id+received_by_id as owner_id from message where created_by_id=:created_by_id or received_by_id=:received_by_id),
      x as (select owner_id,max(id) as id from mcr group by owner_id),
      y as (select m.* from x left join message as m on x.id=m.id)
      select * from y where received_by_id=:received_by_id and status='unread' order by id desc offset :offset limit :limit;
      '''
      values={"created_by_id":request_user['id'],"received_by_id":request_user['id'],"offset":offset,"limit":limit}
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
async def api_func_my_message_thread(x:str,request:Request,user_id:int,page:int,background_tasks:BackgroundTasks):
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
    #background task
    query=f"update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where received_by_id=:received_by_id and created_by_id=:created_by_id returning *;"
    values={"status":"read","updated_by_id":request_user['id'],"updated_at":datetime.now(),"received_by_id":request_user['id'],"created_by_id":user_id}
    background_tasks.add_task(function_query_runner,postgres_object[x],"write",query,values)
    #finally
    return response

@router.delete("/{x}/my-delete")
async def api_func_my_delete(request:Request,x:str,mode:Literal["message_all","message_mutual","message_thread","like_post","bookmark_post"],user_id:int=None,post_id:int=None,message_id:int=None):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    if mode=="message_all":
        query="delete from message where created_by_id=:created_by_id or received_by_id=:received_by_id;"
        values={"created_by_id":request_user['id'],"received_by_id":request_user['id']}
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
    response=await function_query_runner(postgres_object[x],"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #finally
    return {"status":1,"message":"object deleted"}

@router.delete("/{x}/my-delete-account")
async def api_func_my_delete_account(x:str,request:Request,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,config_jwt_secret_key)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #admin check
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
    
