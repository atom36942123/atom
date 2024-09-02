#router
from fastapi import APIRouter
router=APIRouter(tags=["external"])

#s3 create presigned url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_aws
@router.get("/external/s3-create-presigned-url")
async def function_external_s3_create_presigned_url(request:Request,filename:str):
   #logic
   response=await function_aws("s3_create_presigned_url",{"filename":filename})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#ses send email
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_aws
@router.post("/external/ses-send-email")
async def function_external_ses_send_email(request:Request):
   #logic
   body=await request.json()
   response=await function_aws("ses_send_email",body)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#s3 delete single
from fastapi import Request
from fastapi.responses import JSONResponse
from function import function_token_check
from function import function_aws
@router.delete("/external/s3-delete-single")
async def function_external_s3_delete_single(request:Request,url:str):
  #auth check
  if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
  #logic
  response=await function_aws("s3_delete_single",{"url":url})
  if response["status"]==0:return JSONResponse(status_code=400,content=response)
  #final
  return response

#s3 delete all
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_key_root
from function import function_aws
@router.delete("/external/s3-delete-all")
async def function_external_s3_delete_all(request:Request):
  #auth check
  if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content={"status":0,"message":"token root issue"})
  #logic
  response=await function_aws("s3_delete_all",{})
  if response["status"]==0:return JSONResponse(status_code=400,content=response)
  #final
  return response
