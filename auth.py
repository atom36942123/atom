#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

@router.post("/{x}/signup")
async def function_signup(request:Request):
   body=await request.json()
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   return {"status":1,"message":output}

