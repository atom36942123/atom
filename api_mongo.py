#router
from fastapi import APIRouter
router=APIRouter(tags=["mongo"])

#create object
from fastapi import Request
from config import mongo_object
@router.post("/{x}/mongo/create-object")
async def function_mongo_create_object(request:Request,database:str,table:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #mongo object
   
   #request body
   request_body=await request.json()
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.insert_one(request_body)
   #final
   return {"status":1,"message":repr(output.inserted_id)}

#read object
from fastapi import Request
from config import config_mongo_server
import motor.motor_asyncio
from bson import ObjectId
@router.get("/{x}/mongo/read-object")
async def function_mongo_read_object(request:Request,database:str,table:str,id:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server)
   #logic
   if database=="test" and table=="users":
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(id)})
      if output:output['_id']=str(output['_id'])
   #final
   return {"status":1,"message":output}

#update object
from fastapi import Request
from config import config_mongo_server
import motor.motor_asyncio
from bson import ObjectId
@router.put("/{x}/mongo/update-object")
async def function_mongo_update_object(request:Request,database:str,table:str,id:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server)
   #request body
   request_body=await request.json()
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":request_body})
   #final
   return {"status":1,"message":output.modified_count}

#delete object
from fastapi import Request
from config import config_mongo_server
import motor.motor_asyncio
from bson import ObjectId
@router.delete("/{x}/mongo/delete-object")
async def function_mongo_delete_object(request:Request,database:str,table:str,id:str):
   #postgres object
   postgres_object=request.state.postgres_object
   #mongo object
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server)
   #logic
   if database=="test" and table=="users":
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
   #final
   return {"status":1,"message":output.deleted_count}
