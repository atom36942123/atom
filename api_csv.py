#router
from fastapi import APIRouter
router=APIRouter(tags=["csv"])

#create
from fastapi import Request
from config import postgres_object
from fastapi import UploadFile
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/csv/create",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_csv_create(request:Request,table:str,file:UploadFile):
   #auth check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if user["type"]!="admin":return JSONResponse(status_code=400,content={"status":0,"message":"admin issue"})
   #final
   return {"status":1,"message":output}


   
   







