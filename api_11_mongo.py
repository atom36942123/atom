#router
from fastapi import APIRouter
router=APIRouter(tags=["mongo"])

#create object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
@router.post("/{x}/mongo/create-object")
async def function_mongo_create_object(request:Request,database:str,table:str):
   #body
   body=await request.json()
   #mongo object
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
from bson import ObjectId
@router.get("/{x}/mongo/read-object")
async def function_mongo_read_object(request:Request,database:str,table:str,id:str):
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
   #final
   return {"status":1,"message":output}

#update object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
from bson import ObjectId
@router.put("/{x}/mongo/update-object")
async def function_mongo_update_object(request:Request,database:str,table:str,id:str):
   #body
   body=await request.json()
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":body})
   #final
   return {"status":1,"message":output.modified_count}

#delete object
from fastapi import Request
import motor.motor_asyncio
from config import config_mongo_server_uri
from bson import ObjectId
@router.delete("/{x}/mongo/delete-object")
async def function_mongo_delete_object(request:Request,database:str,table:str,id:str):
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
   #final
   return {"status":1,"message":output.deleted_count}
