

#delete object
from fastapi import Request
from config import mongo_object
from bson import ObjectId
@router.delete("/mongo/delete-object")
async def function_mongo_delete_object(request:Request,database:str,table:str,id:str):
   #logic
   if database=="test" and table=="users":
      
   #final
   return {"status":1,"message":output.deleted_count}
