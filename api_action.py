#router
from fastapi import APIRouter
router=APIRouter(tags=["action"])

#import raise error
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#import auth check jwt
from config import config_key_jwt
import jwt
import json

#post
from fastapi import Request
@router.post("/{x}/action/post")
async def function_action_post(request:Request,description:str,title:str=None,file_url:str=None,link_url:str=None,tag:str=None):
   #database 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into post (created_by_id,title,description,file_url,link_url,tag) values (:created_by_id,:title,:description,:file_url,:link_url,:tag) returning *;"
   query_param=dict(request.query_params)|{"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#like
from fastapi import Request
@router.post("/{x}/action/like")
async def function_action_like(request:Request,parent_table:str,parent_id:int):
   #database 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into likes (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param=dict(request.query_params)|{"created_by_id":user["id"]}
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#bookmark
from fastapi import Request
@router.post("/{x}/action/bookmark")
async def function_action_bookmark(request:Request,parent_table:str,parent_id:int):
   #database 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into bookmark (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param=dict(request.query_params)|{"created_by_id":user["id"]}
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
