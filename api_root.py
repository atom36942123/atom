#router
from fastapi import APIRouter
router=APIRouter(tags=["root"])

#root
from postgres import postgres_object_dict
from fastapi import Request
@router.get("/")
async def function_root():
   x_list=[*postgres_object_dict]
   return {"status":1,"message":f"welcome to {x_list}"}
