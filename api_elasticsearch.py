
#search
from fastapi import Request
from config import elasticsearch_object
@router.get("/elasticsearch/search")
async def function_elasticsearch_search(request:Request,table:str,key:str,keyword:str,limit:int=100):
   #logic
   
   #final
   return response
