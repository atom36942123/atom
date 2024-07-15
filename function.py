from fastapi import Request,Response
def request_key_builder(func,namespace: str = "",*,request: Request = None,response: Response = None,**kwargs,):
    return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])
        
async def function_query_runner(postgres_object,mode,query,values):
   #start
   if mode not in ["read","write"]:return {"status":0,"message":"wrong mode"}
   #logic
   if mode=="read":
      try:output=list(map(lambda x:dict(x),await postgres_object.fetch_all(query=query,values=values)))
      except Exception as e:
         print(query)
         return {"status":0,"message":e.args}
   if mode=="write":
      try:output=await postgres_object.execute(query=query,values=values)
      except Exception as e:
         print(query)
         return {"status":0,"message":e.args}
   #final response
   return {"status":1,"message":output}

async def function_object_read(postgres_object,function_query_runner,table,param,order,limit,offset):
   #param set
   param={k:v for k,v in param.items() if v not in [None,""," "]}
   #where set
   where="where "
   for k,v in param.items():
      if k=="tag":where=where+f"({k} @> :{k} or :{k} is null) and "
      elif k=="rating":where=where+f"({k} >= :{k} or :{k} is null) and "
      else:where=where+f"({k} = :{k} or :{k} is null) and "
   where=where.strip().rsplit('and',1)[0]
   if where=="where":where=""
   #logic
   query=f"select * from {table} {where} order by {order[0]} {order[1]} limit {limit} offset {offset};"
   response=await function_query_runner(postgres_object,"read",query,param)
   if response["status"]==0:return response
   #final response
   return response

async def function_param_validation(param):
   #check
   param={k:v for k,v in param.items() if v not in [None,""," "]}
   if not param:return {"status":0,"message":"param is null"}
   #length
   mapping_max_length={
   "type":100,"title":1000,"description":5000,"file_url":1000,"link_url":1000,"tag":10,
   "parent_table":100,
   "status":100,"remark":1000,
   "email":50,"mobile":50,"whatsapp":50,"phone":50,
   "country":50,"state":50,"city":50,
   "username":100,"password":1000,"firebase_id":1000,
   "name":100,"gender":100,"profile_pic_url":1000
   }
   for k,v in param.items():
      if k in mapping_max_length:
         if v and len(v)>mapping_max_length[k]:return {"status":0,"message":f"{k} length should be less than {mapping_max_length[k]}"}
   #validation
   if "username" in param and " " in param["username"]:return {"status":0,"message":"whitespace not allowed in username"}
   if "email" in param and "@" not in param["email"]:return {"status":0,"message":"@ in email is must"}
   if "rating" in param and (param["rating"]<0 or param["rating"]>10):return {"status":0,"message":"0<=rating<1=0"}
   #final response
   return {"status":1,"message":"done"}

import json
async def function_param_conversion(param):
   #check
   param={k:v for k,v in param.items() if v not in [None,""," "]}
   if not param:return {"status":0,"message":"param is null"}
   #logic
   try:
      if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
      if "tag" in param:param["tag"]=[x.strip(' ').lower() for x in param["tag"]]
      if "tag" in param:param["tag"]=[x[1:] if x[0]=="#" else x for x in param["tag"]]
      if "tag" in param:param["tag"]=list(dict.fromkeys(param["tag"]))
      if "number" in param:param["number"]=round(param["number"],5)
   except Exception as e:return {"status":0,"message":e.args}
   #final response
   return {"status":1,"message":param}

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

import uvicorn
import asyncio
def function_server_start(app,host,port):
   #start
   uvicorn_config=uvicorn.Config(app,host,port,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio")
   uvicorn_web_server_object=uvicorn.Server(config=uvicorn_config)
   loop=asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   #logic
   try:
      loop.run_until_complete(uvicorn_web_server_object.serve())
   except Exception as e:print(e.args)
   #final response
   return None

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
def function_http_response(status_code,status,message):
   #message change
   if "unique_action_tcpp" in str(message):message="action alredy performed"
   #logic
   response=JSONResponse(status_code=status_code,content=jsonable_encoder({"status":status,"message":message}))
   #final response
   return response

import jwt
import json
import time
from datetime import datetime,timedelta
async def function_token_encode(data,jwt_expire_day,jwt_secret_key):
   #logic
   try:
      payload={"data":json.dumps(data,default=str),"exp":time.mktime((datetime.now()+timedelta(days=int(jwt_expire_day))).timetuple())}
      token=jwt.encode(payload,jwt_secret_key)
   except Exception as e:return {"status":0,"message":e.args}
   #final response
   return {"status":1,"message":token}

import jwt,json
async def function_token_decode(request,jwt_secret_key):
   #start
   token=request.headers.get("token")
   request_user={}
   x=str(request.url).split("/")[3]
   #logic
   if not token:return {"status":0,"message":"token is must"}
   try:payload=jwt.decode(token,jwt_secret_key,algorithms="HS256")
   except Exception as e:return {"status":0,"message":e.args}
   request_user=json.loads(payload["data"])
   if "x" not in request_user:return {"status":0,"message":"x was not set in token encode while login"}
   if request_user["x"]!=x:return {"status":0,"message":"token x mismatch"}
   #final response
   return {"status":1,"message":request_user}

import boto3
async def function_s3_create_url(aws_s3_bucket_region,aws_access_key_id,aws_secret_access_key,aws_s3_bucket_name,key):
   limit_size_kb=1000
   boto3_client_s3=boto3.client("s3",region_name=aws_s3_bucket_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   try:output=boto3_client_s3.generate_presigned_post(Bucket=aws_s3_bucket_name,Key=key,ExpiresIn=1000,Conditions=[['content-length-range',1,1024*limit_size_kb]])
   except Exception as e:response={"status":0,"message":e.args}
   return {"status":1,"message":output}

import boto3
async def function_s3_delete_url(aws_access_key_id,aws_secret_access_key,aws_s3_bucket_name,url):
   boto3_resource_s3=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   for item in url.split(","):
      key=item.split("/")[-1]
      if not key:continue
      try:output=boto3_resource_s3.Object(aws_s3_bucket_name,key).delete()
      except Exception as e:
         response={"status":0,"message":e.args}
   return {"status":1,"message":output}

import boto3
async def function_ses_send_email(aws_ses_region,aws_access_key_id,aws_secret_access_key,aws_ses_sender,to,title,description):
   boto3_client_ses=boto3.client("ses",region_name=aws_ses_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   try:output=boto3_client_ses.send_email(Source=aws_ses_sender,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   except Exception as e:response={"status":0,"message":e.args}
   return {"status":1,"message":output}

async def function_add_cloudfront_url(aws_s3_bucket_name,aws_cloudfront_url,object_list):
   #check
   if not object_list:return {"status":1,"message":object_list}
   #logic
   url_list=[]
   for index,item in enumerate(object_list):
      if item["file_url"]:
         for url in item["file_url"].split(","):
            if aws_s3_bucket_name in url:url_list.append(aws_cloudfront_url+url.split("/")[-1])
            else:url_list.append(url)
      object_list[index]["file_url"]=",".join(url_list)
      url_list=[]
   #final response
   return {"status":1,"message":object_list}

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
   #logic
   drop_all_view_get_query='''
   select 'drop view if exists ' || string_agg (table_name, ', ') || ' cascade;' as output 
   from information_schema.views 
   where table_schema not in ('pg_catalog', 'information_schema') and table_name !~ '^pg_';
   '''
   response=await function_query_runner(postgres_object,"read",drop_all_view_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}
