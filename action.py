#router
from fastapi import APIRouter
router=APIRouter(tags=["action"])

#post
from config import config_key_jwt
import jwt,json
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/action/post")
async def function_action_post(request:Request):
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
