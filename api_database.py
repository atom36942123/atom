#router
from fastapi import APIRouter
router = APIRouter(tags=["database"])

#import common
from config import *
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#api
@router.get("/{x}/database/qrunner")
async def function_qrunner(request:Request,query:str):
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   query=query
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   return output

