#router
from fastapi import APIRouter
router=APIRouter(tags=["elasticsearch"])

#create object
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.post("/{x}/elasticsearch/create-object")
async def function_elasticsearch_create_object(request:Request,table:str,id:int):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.index(index=table,id=id,document=body)
   #final
   return response

#read object
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.get("/{x}/elasticsearch/read-object")
async def function_elasticsearch_read_object(request:Request,table:str,id:int):
   #prework
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.get(index=table,id=id)
   #final
   return response

#update object
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.put("/{x}/elasticsearch/update-object")
async def function_elasticsearch_update_object(request:Request,table:str,id:int):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.update(index=table,id=id,doc=body)
   #final
   return response

#delete object
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.delete("/{x}/elasticsearch/delete-object")
async def function_elasticsearch_delete_object(request:Request,table:str,id:str):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.delete(index=table,id=id)
   #final
   return response

#refresh table
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.get("/{x}/elasticsearch/refresh-table")
async def function_elasticsearch_refresh_table(request:Request,table:str):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.indices.refresh(index=table)
   #final
   return response

#search
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id,config_elasticsearch_username,config_elasticsearch_password
@router.get("/{x}/elasticsearch/search")
async def function_elasticsearch_search(request:Request,table:str,key:str,keyword:str,limit:int=100):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   response=elasticsearch_object.search(index=table,body={"query":{"match":{key:keyword}},"size":limit})
   #final
   return response
