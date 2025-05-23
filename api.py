#router
from fastapi import APIRouter
router=APIRouter()

#import
from main import *

#ratelimiter
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

#test
@router.get("/test",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def test(request:Request):
   await postgres_create("test",[{"title":"test"}],0,request.state.postgres_client,postgres_column_datatype,object_serialize)
   return {"status":1,"message":"welcome to test"}

