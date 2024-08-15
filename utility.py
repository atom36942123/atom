#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

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
import boto3
@router.get("/{x}/utility/create-presigned-url")
async def function_utility_create_presigned_url(request:Request,filename:str):
   #logic
   boto3_clientclient=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
   output=boto3_clientclient.generate_presigned_post(Bucket=config_s3_bucket_name,Key=str(uuid.uuid4())+"-"+body["filename"],ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])

   
   #final
   return {"status":1,"message":temp}




   #body={"mode":"s3_delete_bucket_key","url":"www.xxx.png/xxx"}
   if body["mode"]=="s3_delete_bucket_key":
      if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
      output=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).Object(config_s3_bucket_name,body["url"].rsplit("/",1)[1]).delete()
   #body={"mode":"s3_delete_bucket_key_all"}
   if body["mode"]=="s3_delete_bucket_key_all":
      if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
      output=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).Bucket(config_s3_bucket_name).objects.all().delete()
   #body={"mode":"ses_send_email","to":"atom36942@gmail.com","title":"xxx","description":"xxx"}
   if body["mode"]=="ses_send_email":
      output=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key).send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[body["to"]]},Message={"Subject":{"Charset":"UTF-8","Data":body["title"]},"Body":{"Text":{"Charset":"UTF-8","Data":body["description"]}}})
   #final
   return {"status":1,"message":output}

