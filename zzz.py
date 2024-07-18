#elasticsearch
from fastapi import Body
from elasticsearch import Elasticsearch

from config import config_elasticsearch_cloud_id
from config import config_elasticsearch_username
from config import config_elasticsearch_password

if False:
   try:elasticsearch_object=Elasticsearch(cloud_id=cloud_id,basic_auth=(username,password))
   except Exception as e:print(e)
@router.post("/{x}/elasticsearch-create-object")
async def function_api(x:str,table:str,id:int,body:dict=Body(...)):
    try:response=elasticsearch_object.index(index=table,id=id,document=body)
    except Exception as e:return function_http_response(400,0,e.args)
    return response
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

