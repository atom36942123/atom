#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
from config import config_postgres_object
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
import hashlib
from function import function_token_create
from config import config_key_jwt
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_auth_signup(request:Request,username:str,password:str):
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await config_postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await function_token_create(user,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

