#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#feed
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from function import function_sanitization_values_list
from function import function_add_creator_key
from function import function_add_action_count
from fastapi_cache.decorator import cache
from function import function_read_redis_key
@router.get("/{x}/utility/feed")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_utility_feed(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #prework
   query_param=dict(request.query_params)
   if table not in ["users","post","atom"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #where
   where_param={k:v for k,v in query_param.items() if k not in ["table","order","limit","page"]}
   where_param_values={k:v.rsplit(',',1)[0] for k,v in where_param.items()}
   where_param_operator={k:v.rsplit(',',1)[1] for k,v in where_param.items()}
   key_list=[f"({k}{where_param_operator[k]}:{k} or :{k} is null)" for k,v in where_param_values.items()]
   key_joined=' and '.join(key_list)
   where=f"where {key_joined}" if key_joined else ""
   #sanitization
   values_list=[where_param_values]
   response=await function_sanitization_values_list(request.state.postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   values=values_list[0]
   #read object
   query=f"select * from {table} {where} order by {order} limit {limit} offset {(page-1)*limit};"
   values=values
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   output=[dict(item) for item in output]
   #add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add action count
   response=await function_add_action_count(request.state.postgres_object,output,table,"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}

#update cell
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
@router.put("/{x}/utility/update-cell")
async def function_utility_update_cell(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   body=dict(await request.json())
   #body unpack
   table=body["table"]
   id=body["id"]
   column=body["column"]
   value=body["value"]
   #logic
   if column in ["password","google_id"]:value=hashlib.sha256(value.encode()).hexdigest()
   if column in ["metadata"]:value=json.dumps(value)
   query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
   values={"value":value,"id":id,"updated_at":datetime.now(),"updated_by_id":user['id']}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#pcache
from fastapi import Request
from fastapi_cache.decorator import cache
@router.get("/{x}/utility/pcache")
@cache(expire=60)
async def function_utility_pcache(request:Request): 
   #logic
   config_pcache={"user_count":"select count(*) from users;"}
   temp={}
   for k,v in config_pcache.items():
      query=v
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   return {"status":1,"message":temp}

#presigned url
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name,config_s3_region_name
import boto3,uuid
@router.get("/{x}/utility/create-presigned-url")
async def function_utility_create_presigned_url(request:Request,filename:str):
   #logic
   s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   buckey_key=str(uuid.uuid4())+"-"+filename
   size_kb=250
   expire_secs=10
   output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=buckey_key,ExpiresIn=expire_secs,Conditions=[['content-length-range',1,size_kb*1024]])
   #final
   return {"status":1,"message":output}

#delete s3 key
from config import config_key_root
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name
import boto3
@router.delete("/{x}/utility/delete-s3-key")
async def function_utility_delete_s3_key(request:Request,url:str):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #logic
   buckey_key=url.rsplit("/",1)[1]
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_resource.Object(config_s3_bucket_name,buckey_key).delete()
   #final
   return {"status":1,"message":output}

#empty s3 bucket
from config import config_key_root
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name
import boto3
@router.delete("/{x}/utility/empty-s3-bucket")
async def function_utility_empty_s3_bucket(request:Request):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_resource.Bucket(config_s3_bucket_name).objects.all().delete()
   #final
   return {"status":1,"message":output}

#send-email-ses
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_ses_sender_email,config_ses_region_name
import boto3
@router.get("/{x}/utility/send-email-ses")
async def function_utility_send_email_ses(request:Request,to:str,title:str,description:str):
   #logic
   ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   #final
   return {"status":1,"message":output}
