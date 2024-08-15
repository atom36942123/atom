#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#api
from fastapi import Request
import hashlib
@router.post("/{x}/auth/signup")
async def function_auth_signup(request:Request):
   body=await request.json()
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   return {"status":1,"message":output}

