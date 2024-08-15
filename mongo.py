#router
from fastapi import APIRouter
router=APIRouter(tags=["mongo"])

from bson import ObjectId

#create object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
@router.post("/{x}/mongo/create-object")
async def function_mongo_create_object(request:Request,database:str,table:str):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(body)
   #final
   return {"status":1,"message":repr(output.inserted_id)}

#read object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
@router.get("/{x}/mongo/read-object")
async def function_mongo_read_object(request:Request,database:str,table:str,id:str):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
   #final
   return {"status":1,"message":output}

#delete object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
@router.delete("/{x}/mongo/delete-object")
async def function_mongo_delete_object(request:Request,database:str,table:str,id:str):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
   #final
   return {"status":1,"message":output.deleted_count}


      
     
      
   # #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob"}
   # #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob","age":100}
   # if body["mode"]=="update":
   #    key_to_update={k:v for k,v in body.items() if k not in ["mode","id"]}
   #    output=await mongo_object.test.users.update_one({"_id":ObjectId(body["id"])},{"$set":key_to_update})
   #    response={"status":1,"message":output.modified_count}
  

# from elasticsearch import Elasticsearch
# @router.post("/{x}/elasticsearch")
# async def function_elasticsearch(request:Request):
#    #prework
#    body=await request.json()
#    elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
#    #logic
#    #body={"mode":"create","table":"users","id":1,"username":"xxx","age":33,"country":"korea"}
#    if body["mode"]=="create":
#       object={k:v for k,v in body.items() if k not in ["mode","table","id"]}
#       response=elasticsearch_object.index(index=body["table"],id=body["id"],document=object)
#    #body={"mode":"read","table":"users","id":"1"}
#    if body["mode"]=="read":
#       response=elasticsearch_object.get(index=body["table"],id=body["id"])
#    #{"mode":"update","table":"users","id":"1","username":"bob","age":100}
#    if body["mode"]=="update":
#       key_to_update={k:v for k,v in body.items() if k not in ["mode","table","id"]}
#       response=elasticsearch_object.update(index=body["table"],id=body["id"],doc=key_to_update)
#    #body={"mode":"delete","table":"users","id":"1"}
#    if body["mode"]=="delete":
#       response=elasticsearch_object.delete(index=body["table"],id=body["id"])
#    #body={"mode":"refresh","table":"users"}
#    if body["mode"]=="refresh":
#       response=elasticsearch_object.indices.refresh(index=body["table"])
#    #body={"mode":"search","table":"users","key":"username","keyword":"xxx","limit":1}
#    if body["mode"]=="search":
#       response=elasticsearch_object.search(index=body["table"],body={"query":{"match":{body["key"]:body["keyword"]}},"size":body["limit"]})
#    #final
#    return response

