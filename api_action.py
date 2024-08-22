#router
from fastapi import APIRouter
router=APIRouter(tags=["action"])

#post
from fastapi import Request
from function import function_token_check_jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/action/post")
async def function_action_post(request:Request,description:str,title:str=None,file_url:str=None,link_url:str=None,tag:str=None):
   #postgres object
   postgres_object=request.state.postgres_object
   #token check jwt
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #logic
   query="insert into post (created_by_id,title,description,file_url,link_url,tag) values (:created_by_id,:title,:description,:file_url,:link_url,:tag) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#helpdesk
from fastapi import Request
@router.post("/{x}/action/helpdesk")
async def function_action_helpdesk(request:Request,type:str,description:str):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into helpdesk (created_by_id,type,description) values (:created_by_id,:type,:description) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#like
from fastapi import Request
@router.post("/{x}/action/like")
async def function_action_like(request:Request,parent_table:str,parent_id:int):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into likes (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#bookmark
from fastapi import Request
@router.post("/{x}/action/bookmark")
async def function_action_bookmark(request:Request,parent_table:str,parent_id:int):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into bookmark (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#block
from fastapi import Request
@router.post("/{x}/action/block")
async def function_action_block(request:Request,parent_table:str,parent_id:int,description:str=None):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into block (created_by_id,parent_table,parent_id,description) values (:created_by_id,:parent_table,:parent_id,:description) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#comment
from fastapi import Request
@router.post("/{x}/action/comment")
async def function_action_comment(request:Request,parent_table:str,parent_id:int,description:str,file_url:str=None,):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into comment (created_by_id,parent_table,parent_id,description,file_url) values (:created_by_id,:parent_table,:parent_id,:description,:file_url) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message
from fastapi import Request
@router.post("/{x}/action/message")
async def function_action_message(request:Request,parent_table:str,parent_id:int,description:str):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into message (created_by_id,parent_table,parent_id,description) values (:created_by_id,:parent_table,:parent_id,:description) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#rating
from fastapi import Request
@router.post("/{x}/action/rating")
async def function_action_rating(request:Request,parent_table:str,parent_id:int,rating:str):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into rating (created_by_id,parent_table,parent_id,rating) values (:created_by_id,:parent_table,:parent_id,:rating) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   query_param["rating"]=float(query_param["rating"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#report
from fastapi import Request
@router.post("/{x}/action/report")
async def function_action_report(request:Request,parent_table:str,parent_id:int,description:str=None):
   #postgres object 
   postgres_object=request.state.postgres_object
   #auth check jwt
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #logic
   query="insert into report (created_by_id,parent_table,parent_id,description) values (:created_by_id,:parent_table,:parent_id,:description) returning *;"
   query_param={"created_by_id":user["id"]}|dict(request.query_params)
   query_param["parent_id"]=int(query_param["parent_id"])
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
