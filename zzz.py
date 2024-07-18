#router
from fastapi import APIRouter
router=APIRouter(tags=["zzz"])

#mongo
import motor.motor_asyncio
from bson import ObjectId
from fastapi import Body
from function import function_http_response
if False:
    try:mongo_object=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    except Exception as e:print(e)
@router.post("/{x}/mongo-create-object")
async def function_api(x:str,database:str,table:str,body:dict=Body(...)):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.insert_one(body)
        except Exception as e:return function_http_response(400,0,e.args)
    return {"status":1,"message":str((response.inserted_id))}
@router.get("/{x}/mongo-read-object")
async def function_api(x:str,database:str,table:str,id:str):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.find_one({"_id": ObjectId(id)})
        except Exception as e:return function_http_response(400,0,e.args)
        if response:response['_id']=str(response['_id'])
    return response
@router.put("/{x}/mongo-update-object")
async def function_api(x:str,database:str,table:str,id:str,body:dict=Body(...)):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":body})
        except Exception as e:return function_http_response(400,0,e.args)
    return response.modified_count
@router.delete("/{x}/mongo-delete-object")
async def function_api(x:str,database:str,table:str,id:str):
    if database=="test" and table=="users":
        try:response=await mongo_object.test.users.delete_one({"_id":ObjectId(id)})
        except Exception as e:return function_http_response(400,0,e.args)
    return response.deleted_count


#elasticsearch
from object import elasticsearch_object
from fastapi import Body
from function import function_http_response
@router.post("/{x}/elasticsearch-create-object")
async def function_api(x:str,table:str,id:int,body:dict=Body(...)):
    try:response=elasticsearch_object.index(index=table,id=id,document=body)
    except Exception as e:return function_http_response(400,0,e.args)
    return response


#elasticsearch
from elasticsearch import Elasticsearch
from config import config_elasticsearch_cloud_id
from config import config_elasticsearch_username
from config import config_elasticsearch_password
elasticsearch_object=None
if False:
   try:elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   except Exception as e:print(e)

@router.get("/{x}/elasticsearch-read-object")
async def function_api(x:str,table:str,id:int):
    try:response=elasticsearch_object.get(index=table,id=id)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.put("/{x}/elasticsearch-update-object")
async def function_api(x:str,table:str,id:int,body:dict=Body(...)):
    try:response=elasticsearch_object.update(index=table,id=id,doc=body)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.delete("/{x}/elasticsearch-delete-object")
async def function_api(x:str,table:str,id:int):
    try:response=elasticsearch_object.delete(index=table,id=id)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.get("/{x}/elasticsearch-refresh-table")
async def function_api(x:str,table:str):
    try:response=elasticsearch_object.indices.refresh(index=table)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.get("/{x}/elasticsearch-search")
async def function_api(x:str,table:str,column:str,keyword:str):
    query={"query":{"match":{column:keyword}},"size":30}
    try:response=elasticsearch_object.search(index=table,body=query)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

