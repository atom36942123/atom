from fastapi import BackgroundTasks
from function import function_postgres_add_creator_key
from function import function_postgres_add_action_count

from datetime import datetime
from function import function_message_read
from function import function_object_update
@router.get("/my/message-read")
async def function_my_message_read(request:Request,background:BackgroundTasks,mode:str,order:str="id desc",limit:int=100,page:int=1,user_id:int=None):
   #auth
   response=await function_auth("jwt",request,config_key_root,config_key_jwt,postgres_object,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_message_read(postgres_object,"users",mode,user["id"],user_id,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #background
   if mode=="thread":
      query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"parent_id":user["id"]}
      background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   if mode in ["received","received_unread"]:
      object_list=[]
      for item in output:
         object={"id":item["id"],"status":"read","updated_by_id":user["id"]}
         object_list.append(object)
      response=await function_object_update(postgres_object,"background","message",object_list)
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

from function import function_message_delete
@router.delete("/my/message-delete")
async def function_my_message_delete(request:Request,mode:str,id:int=None):
   #auth
   response=await function_auth("jwt",request,config_key_root,config_key_jwt,postgres_object,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await function_message_delete(postgres_object,"users",mode,user["id"],id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_otp_verify
from function import function_object_update
@router.put("/my/update-contact")
async def function_my_update_contact(request:Request,otp:int,email:str=None,mobile:str=None):
   #auth
   response=await function_auth("jwt",request,config_key_root,config_key_jwt,postgres_object,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #otp verify
   if email and mobile:return JSONResponse(status_code=400,content={"status":0,"message":"send either email or mobile"})
   response=await function_otp_verify(postgres_object,otp,email,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #logic
   if email:object={"id":user["id"],"updated_by_id":user["id"],"email":email}
   if mobile:object={"id":user["id"],"updated_by_id":user["id"],"mobile":mobile}
   response=await function_object_update(postgres_object,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

import random
from function import function_sns
from function import function_ses
@router.get("/utility/otp-send")
async def function_utility_otp_send(request:Request,mode:str,email:str=None,mobile:str=None):
   #logic
   otp=random.randint(100000,999999)
   if email and mobile:return JSONResponse(status_code=400,content={"status":0,"message":"send either email/mobile"})
   if not email and not mobile:return JSONResponse(status_code=400,content={"status":0,"message":"email/mobile both cant be null"})
   if mode=="ses":response=await function_ses("send_email",{"to":email,"title":"otp","description":f"otp={otp}"})
   if mode=="sns":response=await function_sns("send_sms",{"mobile":mobile,"message":f"otp={otp}"})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #save otp
   query="insert into otp (otp,email,mobile) values (:otp,:email,:mobile) returning *;"
   query_param={"otp":otp,"email":email,"mobile":mobile}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"otp sent"}

from function import function_otp_verify
@router.get("/utility/otp-verify")
async def function_utility_otp_verify(request:Request,otp:int,email:str=None,mobile:str=None):
   #logic
   response=await function_otp_verify(postgres_object,otp,email,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_s3
@router.get("/utility/file")
async def function_utility_file(request:Request,mode:str,filename:str=None,url:str=None):
   #logic
   if mode=="create_s3":
      response=await function_s3("create",{"filename":filename})
   if mode=="delete_s3":
      response=await function_auth("jwt",request,postgres_object,1,["admin"])
      if response["status"]==0:return JSONResponse(status_code=400,content=response)
      user=response["message"]
      response=await function_s3("delete",{"url":url})
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

from function import function_where_clause
from function import function_location_search
@router.get("/utility/location-search")
async def function_utility_location_search(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #where clause
   request_query_param=dict(request.query_params)
   response=await function_where_clause(request_query_param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   response=await function_location_search(postgres_object,table,where_string,where_param,location,within,order,limit,(page-1)*limit)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#admin
from function import function_where_clause
@router.get("/admin/object-read")
async def function_admin_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #auth
   response=await function_auth("jwt",request,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #where clause
   request_query_param=dict(request.query_params)
   response=await function_where_clause(request_query_param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

from function import function_object_update
@router.put("/admin/object-update")
async def function_admin_object_update(request:Request,table:str):
   #auth
   response=await function_auth("jwt",request,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #object
   object=await request.json()
   object["updated_by_id"]=user["id"]
   #object check
   if table in ["spatial_ref_sys","otp","log"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   #logic
   response=await function_object_update(postgres_object,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#public
from function import function_where_clause
@router.get("/public/object-read")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_public_object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #where clause
   request_query_param=dict(request.query_params)
   response=await function_where_clause(request_query_param)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_param=response["message"][0],response["message"][1]
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_param
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #add creator key
   response=await function_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #add action count
   response=await function_postgres_add_action_count(postgres_object,"likes",output,table)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   #final
   return {"status":1,"message":output}
   
@router.get("/public/read-ids")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_public_read_ids(request:Request,table:str,ids:str):
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   query=f"select * from {table} where id in ({ids}) order by id desc;"
   query_param={}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}
