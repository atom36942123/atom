#router
from fastapi import APIRouter
router=APIRouter(tags=["action"])

#create post
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-post")
async def function_action_create_post(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   type=request_body["type"]
   title=request_body["title"]
   description=request_body["description"]
   file_url=request_body["file_url"]
   link_url=request_body["link_url"]
   tag=request_body["tag"]
   #logic
   query="insert into post (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;"
   query_param={"created_by_id":user["id"],"type":type,"title":title,"description":description,"file_url":file_url,"link_url":link_url,"tag":tag}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#helpdesk
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-helpdesk")
async def function_action_create_helpdesk(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   type=request_body["type"]
   description=request_body["description"]
   email=request_body["email"]
   mobile=request_body["mobile"]
   #logic
   query="insert into helpdesk (created_by_id,type,description,email,mobile) values (:created_by_id,:type,:description,:email,:mobile) returning *;"
   query_param={"created_by_id":user["id"],"type":type,"description":description,"email":email,"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#like
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-like")
async def function_action_create_like(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   #logic
   query="insert into likes (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#bookmark
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-bookmark")
async def function_action_create_bookmark(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   #logic
   query="insert into bookmark (created_by_id,parent_table,parent_id) values (:created_by_id,:parent_table,:parent_id) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#block
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-block")
async def function_action_create_block(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   description=request_body["description"]
   #logic
   query="insert into block (created_by_id,parent_table,parent_id,description) values (:created_by_id,:parent_table,:parent_id,:description) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id,"description":description}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#comment
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-comment")
async def function_action_create_comment(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   description=request_body["description"]
   file_url=request_body["file_url"]
   #logic
   query="insert into comment (created_by_id,parent_table,parent_id,description,file_url) values (:created_by_id,:parent_table,:parent_id,:description,:file_url) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id,"description":description,"file_url":file_url}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-message")
async def function_action_create_message(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   description=request_body["description"]
   file_url=request_body["file_url"]
   #logic
   query="insert into message (created_by_id,parent_table,parent_id,description,file_url) values (:created_by_id,:parent_table,:parent_id,:description,:file_url) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id,"description":description,"file_url":file_url}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#rating
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-rating")
async def function_action_create_rating(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   rating=round(request_body["rating"],3)
   #logic
   query="insert into rating (created_by_id,parent_table,parent_id,rating) values (:created_by_id,:parent_table,:parent_id,:rating) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id,"rating":rating}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#report
from fastapi import Request
from config import postgres_object
from function import function_token_check
from fastapi.responses import JSONResponse
@router.post("/{x}/action/create-report")
async def function_action_create_report(request:Request):
   #token check
   response=await function_token_check(request)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #request body
   request_body=await request.json()
   parent_table=request_body["parent_table"]
   parent_id=request_body["parent_id"]
   description=request_body["description"]
   #logic
   query="insert into report (created_by_id,parent_table,parent_id,description) values (:created_by_id,:parent_table,:parent_id,:description) returning *;"
   query_param={"created_by_id":user["id"],"parent_table":parent_table,"parent_id":parent_id,"description":description}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
