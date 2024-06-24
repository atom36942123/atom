#impport
from object import *
from function import function_http_response
from bson import ObjectId
from fastapi import Body

#router
from fastapi import APIRouter
router=APIRouter(tags=["zzz"])

#mongo
@router.post("/{x}/mongo-create-object")
async def api_func(x:str,database:str,table:str,body:dict=Body(...)):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.insert_one(body)
        except Exception as e:return function_http_response(400,0,e.args)
    return {"status":1,"message":str((response.inserted_id))}
    
@router.get("/{x}/mongo-read-object")
async def api_func(x:str,database:str,table:str,id:str):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.find_one({"_id": ObjectId(id)})
        except Exception as e:return function_http_response(400,0,e.args)
        if response:response['_id']=str(response['_id'])
    return response
    
@router.put("/{x}/mongo-update-object")
async def api_func(x:str,database:str,table:str,id:str,body:dict=Body(...)):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":body})
        except Exception as e:return function_http_response(400,0,e.args)
    return response.modified_count
 
@router.delete("/{x}/mongo-delete-object")
async def api_func(x:str,database:str,table:str,id:str):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
        except Exception as e:return function_http_response(400,0,e.args)
    return response.deleted_count

