
#mongo
from config import config_mongo_url
import motor.motor_asyncio
mongo_object=None
if False:
   try:mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_url)
   except Exception as e:print(e)

#elasticsearch
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id
from config import config_elasticsearch_username
from config import config_elasticsearch_password
elasticsearch_object=None
if False:
   try:elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   except Exception as e:print(e)
