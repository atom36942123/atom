#router
from fastapi import APIRouter
router=APIRouter(tags=["elasticsearch"])

#create object
from fastapi import Request
from config import elasticsearch_object
@router.post("/elasticsearch/create-object")
async def function_elasticsearch_create_object(request:Request,table:str,id:int):
   #request body
   request_body=await request.json()
   #logic
   response=elasticsearch_object.index(index=table,id=id,document=request_body)
   #final
   return response

#read object
from fastapi import Request
from config import elasticsearch_object
@router.get("/elasticsearch/read-object")
async def function_elasticsearch_read_object(request:Request,table:str,id:int):
   #logic
   response=elasticsearch_object.get(index=table,id=id)
   #final
   return response

#update object
from fastapi import Request
from config import elasticsearch_object
@router.put("/elasticsearch/update-object")
async def function_elasticsearch_update_object(request:Request,table:str,id:int):
   #request body
   request_body=await request.json()
   #logic
   response=elasticsearch_object.update(index=table,id=id,doc=request_body)
   #final
   return response

#delete object
from fastapi import Request
from config import elasticsearch_object
@router.delete("/elasticsearch/delete-object")
async def function_elasticsearch_delete_object(request:Request,table:str,id:int):
   #logic
   response=elasticsearch_object.delete(index=table,id=id)
   #final
   return response

#refresh table
from fastapi import Request
from config import elasticsearch_object
@router.get("/elasticsearch/refresh-table")
async def function_elasticsearch_refresh_table(request:Request,table:str):
   #logic
   response=elasticsearch_object.indices.refresh(index=table)
   #final
   return response

#search
from fastapi import Request
from config import elasticsearch_object
@router.get("/elasticsearch/search")
async def function_elasticsearch_search(request:Request,table:str,key:str,keyword:str,limit:int=100):
   #logic
   response=elasticsearch_object.search(index=table,body={"query":{"match":{key:keyword}},"size":limit})
   #final
   return response
