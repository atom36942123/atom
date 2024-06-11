#redis
from config import config_redis_url
from redis import asyncio as aioredis
try:redis_object=aioredis.from_url(config_redis_url,encoding="utf-8",decode_responses=True)
except Exception as e:print(e)

#postgres
from config import config_postgres_instance
from config import config_x
from databases import Database
postgres_object={}
for item in config_x:
   try:postgres_object[item]=Database(config_postgres_instance+"/"+item,min_size=1,max_size=100)
   except Exception as e:print(e)

#mongo
from config import config_mongo_url
from config import config_switch_mongo
import motor.motor_asyncio
mongo_object=None
if config_switch_mongo:
   try:mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_url)
   except Exception as e:print(e)

#elasticsearch
from config import config_elasticsearch_cloud_id
from config import config_elasticsearch_username
from config import config_elasticsearch_password
from config import config_switch_elasticsearch
from elasticsearch import Elasticsearch
elasticsearch_object=None
if config_switch_elasticsearch:
   try:elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   except Exception as e:print(e)
   
