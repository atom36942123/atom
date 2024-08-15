#router
from fastapi import APIRouter
router=APIRouter(tags=["elasticsearch"])


#create object
from fastapi import Request
from elasticsearch import Elasticsearch
from config import config_mongo_server_uri
@router.post("/{x}/elasticsearch/create-object")
async def function_elasticsearch_create_object(request:Request,database:str,table:str):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(body)
   #final
   return {"status":1,"message":repr(output.inserted_id)}






   #body={"mode":"create","table":"users","id":1,"username":"xxx","age":33,"country":"korea"}
   if body["mode"]=="create":
      object={k:v for k,v in body.items() if k not in ["mode","table","id"]}
      response=elasticsearch_object.index(index=body["table"],id=body["id"],document=object)
   #body={"mode":"read","table":"users","id":"1"}
   if body["mode"]=="read":
      response=elasticsearch_object.get(index=body["table"],id=body["id"])
   #{"mode":"update","table":"users","id":"1","username":"bob","age":100}
   if body["mode"]=="update":
      key_to_update={k:v for k,v in body.items() if k not in ["mode","table","id"]}
      response=elasticsearch_object.update(index=body["table"],id=body["id"],doc=key_to_update)
   #body={"mode":"delete","table":"users","id":"1"}
   if body["mode"]=="delete":
      response=elasticsearch_object.delete(index=body["table"],id=body["id"])
   #body={"mode":"refresh","table":"users"}
   if body["mode"]=="refresh":
      response=elasticsearch_object.indices.refresh(index=body["table"])
   #body={"mode":"search","table":"users","key":"username","keyword":"xxx","limit":1}
   if body["mode"]=="search":
      response=elasticsearch_object.search(index=body["table"],body={"query":{"match":{body["key"]:body["keyword"]}},"size":body["limit"]})
   #final
   return response

