






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
#s3
from config import aws_default_region,aws_access_key_id,aws_secret_access_key
from config import  s3_bucket_name
import boto3,uuid
async def function_s3(mode,payload):
  s3_client=boto3.client("s3",region_name=aws_default_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
  s3_resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
  if mode=="create":
    filename=payload["filename"]
    key=str(uuid.uuid4())+"-"+filename
    output=s3_client.generate_presigned_post(Bucket=s3_bucket_name,Key=key,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
  if mode=="delete":
    url=payload["url"]
    key=url.rsplit("/",1)[1]
    output=s3_resource.Object(s3_bucket_name,key).delete()
  if mode=="delete_all":
    output=s3_resource.Bucket(s3_bucket_name).objects.all().delete()
  return {"status":1,"message":output}








