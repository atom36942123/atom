#elasticsearch
from config import config_elasticsearch_username,config_elasticsearch_password,config_elasticsearch_cloud_id
from elasticsearch import Elasticsearch
async def function_elasticsearch(mode,table,payload):
  elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
  if mode=="create":
    id,data=payload["id"],payload["data"]
    output=elasticsearch_object.index(index=table,id=id,document=data)
  if mode=="read":
    id=payload["id"]
    response=elasticsearch_object.get(index=table,id=id)
  if mode=="update":
    id,data=payload["id"],payload["data"]
    response=elasticsearch_object.update(index=table,id=id,doc=request_body)
  if mode=="delete":
    id=payload["id"]
    response=elasticsearch_object.delete(index=table,id=id)
  if mode=="refresh_table":
    response=elasticsearch_object.indices.refresh(index=table)
  if mode=="search":
    key,value,limit=payload["key"],payload["value"],payload["limit"]
    response=elasticsearch_object.search(index=table,body={"query":{"match":{key:value}},"size":limit})
  return {"status":1,"message":output}
  
#mongo
from config import config_mongo_server_url
import motor.motor_asyncio
from bson import ObjectId
async def function_mongo(mode,database,table,payload):
  mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_url)
  if mode=="create":
    if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(payload)
      output={"status":1,"message":repr(output.inserted_id)}
  if mode=="read":
    if database=="test" and table=="users":
      id=payload["id"]
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
  if mode=="update":
    if database=="test" and table=="users":
      id,data=payload["id"],payload["data"]
      output=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":data})
      output={"status":1,"message":output.modified_count}
  if mode=="delete":
    if database=="test" and table=="users":
      id=payload["id"]
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
      output={"status":1,"message":output.deleted_count}
  return {"status":1,"message":output}
  
#aws
from config import config_aws_access_key_id,config_aws_secret_access_key
from config import  config_s3_bucket_name,config_s3_region_name
from config import config_ses_sender_email,config_ses_region_name
import boto3,uuid
async def function_aws(mode,payload):
  s3_client=boto3.client("s3",region_name=config_s3_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  s3_resource=boto3.resource("s3",aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  ses_client=boto3.client("ses",region_name=config_ses_region_name,aws_access_key_id=config_aws_access_key_id,aws_secret_access_key=config_aws_secret_access_key)
  if mode=="s3_create_presigned_url":
    filename=payload["filename"]
    key=str(uuid.uuid4())+"-"+filename
    output=s3_client.generate_presigned_post(Bucket=config_s3_bucket_name,Key=key,ExpiresIn=10,Conditions=[['content-length-range',1,250*1024]])
  if mode=="ses_send_email":
    to,title,description=payload["to"],payload["title"],payload["description"]
    output=ses_client.send_email(Source=config_ses_sender_email,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
  if mode=="s3_delete_single":
    url=payload["url"]
    key=url.rsplit("/",1)[1]
    output=s3_resource.Object(config_s3_bucket_name,key).delete()
  if mode=="s3_delete_all":
    output=s3_resource.Bucket(config_s3_bucket_name).objects.all().delete()
  return {"status":1,"message":output}
