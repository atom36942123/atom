#router
from fastapi import APIRouter
router=APIRouter()

#common
from fastapi import Request
from config import config_postgres_object

#token create
from config import config_key_jwt
from function import function_token_create

#rate limiter
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends

#auth
import hashlib
@router.post("/auth/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_auth_signup(request:Request):
   #request body
   request_body=await request.json()
   username=request_body["username"]
   password=str(request_body["password"])
   password=hashlib.sha256(password.encode()).hexdigest()
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":password}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #read user
   user_id=output[0]["id"]
   query="select * from users where id=:id;"
   query_param={"id":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0]
   #token create
   response=await function_token_create(user,config_key_jwt)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}
