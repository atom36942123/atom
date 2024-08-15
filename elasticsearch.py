#router
from fastapi import APIRouter
router=APIRouter(tags=["elasticsearch"])

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

