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
async def function_action_post(request:Request,title:str=None,description:str,file_url:str=None,link_url:str=None,tag:str=None):
   #token check
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into post (title,description,file_url,link_url,tag) values (:title,:description,:file_url,:link_url,:tag) returning *;"
   values=
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}
