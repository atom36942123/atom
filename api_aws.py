#router
from fastapi import APIRouter
router=APIRouter(tags=["aws"])

#presigned url
from fastapi import Request
import boto3,uuid
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name,config_s3_region_name
@router.get("/{x}/aws/create-presigned-url")
async def function_aws_create_presigned_url(request:Request,filename:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #config
   size_kb=250
   expire_secs=10
   #bucket key
   buckey_key=str(uuid.uuid4())+"-"+filename
   #logic
   s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=buckey_key,ExpiresIn=expire_secs,Conditions=[['content-length-range',1,size_kb*1024]])
   #final
   return {"status":1,"message":output}

#send-email-ses
from fastapi import Request
import boto3
from config import config_aws_access_key_id,config_aws_secret_access_key,config_ses_sender_email,config_ses_region_name
@router.post("/{x}/aws/send-email-ses")
async def function_aws_send_email_ses(request:Request):
   #postgres object
   postgres_object=request.state.postgres_object
   #request body
   request_body=await request.json()
   to=request_body["to"]
   title=request_body["title"]
   description=request_body["description"]
   #logic
   ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   #final
   return {"status":1,"message":output}

#delete s3 url
from fastapi import Request
from function import function_token_check
import boto3
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/aws/delete-s3-url")
async def function_aws_delete_s3_url(request:Request,url:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check root
   response=await function_token_check_root(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   #buckey key
   buckey_key=url.rsplit("/",1)[1]
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_resource.Object(config_s3_bucket_name,buckey_key).delete()
   #final
   return {"status":1,"message":output}

#empty s3 bucket
from fastapi import Request
from function import function_token_check
import boto3
from config import config_aws_access_key_id,config_aws_secret_access_key
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.delete("/{x}/aws/empty-s3-bucket")
async def function_aws_empty_s3_bucket(request:Request,bucket_name:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check root
   response=await function_token_check_root(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_resource.Bucket(bucket_name).objects.all().delete()
   #final
   return {"status":1,"message":output}
