#router
from fastapi import APIRouter
router=APIRouter(tags=["action"])

#post
from fastapi import Request
import hashlib
@router.post("/{x}/action/post")
async def function_action_post(request:Request):
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
