import random
from function import function_sns
from function import function_ses
@router.get("/utility/otp-send")
async def function_utility_otp_send(request:Request,mode:str,email:str=None,mobile:str=None):
   #logic
   otp=random.randint(100000,999999)
   if email and mobile:return JSONResponse(status_code=400,content={"status":0,"message":"send either email/mobile"})
   if not email and not mobile:return JSONResponse(status_code=400,content={"status":0,"message":"email/mobile both cant be null"})
   if mode=="ses":response=await function_ses("send_email",{"to":email,"title":"otp","description":f"otp={otp}"})
   if mode=="sns":response=await function_sns("send_sms",{"mobile":mobile,"message":f"otp={otp}"})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #save otp
   query="insert into otp (otp,email,mobile) values (:otp,:email,:mobile) returning *;"
   query_param={"otp":otp,"email":email,"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"otp sent"}

from function import function_otp_verify
@router.get("/utility/otp-verify")
async def function_utility_otp_verify(request:Request,otp:int,email:str=None,mobile:str=None):
   #logic
   response=await function_otp_verify(postgres_object,otp,email,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_s3
@router.get("/utility/file")
async def function_utility_file(request:Request,mode:str,filename:str=None,url:str=None):
   #logic
   if mode=="create_s3":
      response=await function_s3("create",{"filename":filename})
   if mode=="delete_s3":
      response=await function_auth("jwt",request,postgres_object,1,["admin"])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
      response=await function_s3("delete",{"url":url})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response



########################

#sns
from config import config_aws_default_region,config_aws_access_key_id,config_aws_secret_access_key
async def function_sns(mode,payload):
  sns_client=boto3.client("sns",region_name=config_aws_default_region,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="send_sms":
    mobile,message=payload["mobile"],payload["message"]
    output=sns_client.publish(PhoneNumber=mobile,Message=message)
  return {"status":1,"message":output}

#ses
from config import config_aws_default_region,config_aws_access_key_id,config_aws_secret_access_key
from config import config_ses_sender_email
import boto3
async def function_ses(mode,payload):
  ses_client=boto3.client("ses",region_name=config_aws_default_region,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="send_email":
    to,title,description=payload["to"],payload["title"],payload["description"]
    output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
  return {"status":1,"message":output}

#s3
from config import config_aws_default_region,config_aws_access_key_id,config_aws_secret_access_key
from config import  config_s3_bucket_name
import boto3,uuid
async def function_s3(mode,payload):
  s3_client=boto3.client("s3",region_name=config_aws_default_region,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="create":
    filename=payload["filename"]
    key=str(uuid.uuid4())+"-"+filename
    output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=key,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
  if mode=="delete":
    url=payload["url"]
    key=url.rsplit("/",1)[1]
    output=s3_resource.Object(config_s3_bucket_name,key).delete()
  if mode=="delete_all":
    output=s3_resource.Bucket(config_s3_bucket_name).objects.all().delete()
  return {"status":1,"message":output}








