#router
from fastapi import APIRouter
router=APIRouter(tags=["aws"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check root
from config import config_key_root

#presigned url
from fastapi import Request
import boto3
import uuid
from config import config_aws_access_key_id,config_aws_secret_access_key
import config_s3_bucket_name,config_s3_region_name
@router.get("/{x}/aws/create-presigned-url")
async def function_aws_create_presigned_url(request:Request,filename:str):
   #param
   buckey_key=str(uuid.uuid4())+"-"+filename
   size_kb=250
   expire_secs=10
   #logic
   s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=buckey_key,ExpiresIn=expire_secs,Conditions=[['content-length-range',1,size_kb*1024]])
   #final
   return {"status":1,"message":output}

#delete s3 key
from config import config_key_root
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name
import boto3
@router.delete("/{x}/aws/delete-s3-key")
async def function_aws_delete_s3_key(request:Request,url:str):
   #token check
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #param
   buckey_key=url.rsplit("/",1)[1]
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=s3_resource.Object(config_s3_bucket_name,buckey_key).delete()
   #final
   return {"status":1,"message":output}

#empty s3 bucket
from config import config_key_root
from fastapi import Request
from config import config_aws_access_key_id,config_aws_secret_access_key,config_s3_bucket_name
import boto3
@router.delete("/{x}/aws/empty-s3-bucket")
async def function_aws_empty_s3_bucket(request:Request):
   #token check
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
@router.get("/{x}/aws/send-email-ses")
async def function_aws_send_email_ses(request:Request,to:str,title:str,description:str):
   #logic
   ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   #final
   return {"status":1,"message":output}
