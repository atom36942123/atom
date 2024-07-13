#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request

#router
from fastapi import APIRouter
router_root=APIRouter(tags=["root"])

#root
@router_root.get("/")
async def function_api_root():
   return {"status":1,"message":"welcome to atom"}
