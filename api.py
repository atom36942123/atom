
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch



@router.post("/{x}/read")
async def function_read(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #read object
   body["created_by_id"]=user["id"]
   response=await function_read_object(request.state.postgres_object,body)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}


@router.get("/{x}/feed")
@cache(expire=60,key_builder=function_read_redis_key)
async def function_feed(request:Request):
   #prework
   body=dict(request.query_params)
   if body['table'] not in ["users","post","atom"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #read object
   response=await function_read_object(request.state.postgres_object,body)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #add action count
   response=await function_add_action_count(request.state.postgres_object,output,body["table"],"likes")
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":output}



@router.post("/{x}/mongo")
async def function_mongo(request:Request):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server_uri)
   #logic
   #body={"mode":"create","username":"xxx","age":33,"country":"korea"}
   if body["mode"]=="create":
      object={k:v for k,v in body.items() if k not in ["mode"]}
      output=await mongo_object.test.users.insert_one(object)
      response={"status":1,"message":repr(output.inserted_id)}
   #body={"mode":"read","id":"66b36a8a94d4da9c7652ef08"}
   if body["mode"]=="read":
      output=response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
      if output:output['_id']=str(output['_id'])
      response={"status":1,"message":output}
   #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob"}
   #{"mode":"update","id":"66b363e917e01888164aa381","username":"bob","age":100}
   if body["mode"]=="update":
      key_to_update={k:v for k,v in body.items() if k not in ["mode","id"]}
      output=await mongo_object.test.users.update_one({"_id":ObjectId(body["id"])},{"$set":key_to_update})
      response={"status":1,"message":output.modified_count}
   #body={"mode":"delete","id":"66b36a8a94d4da9c7652ef08"}
   if body["mode"]=="delete":
      output=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
      response={"status":1,"message":output.deleted_count}
   #final
   return response

@router.post("/{x}/elasticsearch")
async def function_elasticsearch(request:Request):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))
   #logic
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

