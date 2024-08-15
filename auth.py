#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])


from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/signup")
async def function_signup(request:Request):
   body=await request.json()
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   return {"status":1,"message":output}

