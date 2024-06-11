#impport
from object import elasticsearch_object
from function import function_http_response
from fastapi import Body

#router
from fastapi import APIRouter
router=APIRouter(tags=["elasticsearch"])

#api
@router.post("/{x}/elasticsearch-create-object")
async def api_func(x:str,table:str,id:int,body:dict=Body(...)):
    try:response=elasticsearch_object.index(index=table,id=id,document=body)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.get("/{x}/elasticsearch-read-object")
async def api_func(x:str,table:str,id:int):
    try:response=elasticsearch_object.get(index=table,id=id)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.put("/{x}/elasticsearch-update-object")
async def api_func(x:str,table:str,id:int,body:dict=Body(...)):
    try:response=elasticsearch_object.update(index=table,id=id,doc=body)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.delete("/{x}/elasticsearch-delete-object")
async def api_func(x:str,table:str,id:int):
    try:response=elasticsearch_object.delete(index=table,id=id)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.get("/{x}/elasticsearch-refresh-table")
async def api_func(x:str,table:str):
    try:response=elasticsearch_object.indices.refresh(index=table)
    except Exception as e:return function_http_response(400,0,e.args)
    return response

@router.get("/{x}/elasticsearch-search")
async def api_func(x:str,table:str,column:str,keyword:str):
    query={"query":{"match":{column:keyword}},"size":30}
    try:response=elasticsearch_object.search(index=table,body=query)
    except Exception as e:return function_http_response(400,0,e.args)
    return response
