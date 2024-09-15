#router
from fastapi import APIRouter
router=APIRouter(tags=["api"])

#root
from fastapi import Request
from fastapi.responses import JSONResponse
@router.get("/")
async def root(request:Request):
  return {"status":1,"message":"welcome to atom"}

#postgres-init
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgres_init
@router.get("/postgres-init")
async def postgresinit(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_init(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#signup
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
@router.post("/signup",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def signup(request:Request,username:str,password:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #create user
   query="insert into users (username,password) values (:username,:password) returning *;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=user=output[0]
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":[user,token]}

#login
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
@router.post("/login")
async def login(request:Request,username:str,password:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query=f"select * from users where username=:username and password=:password order by id desc limit 1;"
   query_param={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login google
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgres_read_user_force
@router.post("/login-google")
async def login_google(request:Request,google_id:str,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_read_user_force(postgres_object,"google_id",google_id)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login email
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.post("/login-email")
async def login_email(request:Request,email:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"email",email)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#login mobile
from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from function import token_create
from config import jwt_secret_key
from function import postgtes_otp_verify
@router.post("/login-mobile")
async def login_mobile(request:Request,mobile:str,otp:int,type:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   response=await postgres_read_user_force(postgres_object,"mobile",mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   if type and user["type"] not in type.split(","):return JSONResponse(status_code=400,content={"status":0,"message":f"only {type} can login"})
   #token create
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   token=response["message"]
   #final
   return {"status":1,"message":token}

#profile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from datetime import datetime
from function import postgres_object_update
@router.get("/profile")
async def profile(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response={"status":1,"message":user}
   #update last active at
   object={"id":user["id"],"last_active_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
   await postgres_object_update(postgres_object,column_datatype,"background","users",[object])
   #final
   return response

#token refresh
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import token_create
@router.get("/token-refresh")
async def token_refresh(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query="select * from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   response=await token_create(user,jwt_secret_key)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#exit
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.delete("/exit")
async def exit(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,postgres_object,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if not user:return JSONResponse(status_code=400,content={"status":0,"message":"no user"})
   if user["is_protected"]==1:return {"status":1,"message":"protected user cant deleted"}
   if user["type"] in ["admin"]:return {"status":1,"message":"type admin cant deleted"}
   query="delete from users where id=:id;"
   query_param={"id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":"account deleted"}
   #final
   return response

#postgres clean
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_clean
@router.delete("/postgres-clean")
async def postgresclean(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgres_clean(postgres_object)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#csv create
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_create
@router.post("/csv-create")
async def csv_create(request:Request,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#csv update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import UploadFile
from function import csv_to_object_list
from function import postgres_object_update
@router.post("/csv-update")
async def csv_update(request:Request,table:str,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #file
   response=await csv_to_object_list(file)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object_list=response["message"]
   #logic
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#query runner
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.get("/query-runner")
async def query_runner(request:Request,query:str,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if not mode:output=await postgres_object.fetch_all(query=query,values={})
   if mode=="bulk":output=[await postgres_object.fetch_all(query=item,values={}) for item in query.split("---")]
   #final
   return {"status":1,"message":output}

#project cache
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from function import redis_key_builder
@router.get("/project-cache")
@cache(expire=60,key_builder=redis_key_builder)
async def project_cache(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   query_dict={"user_count":"select count(*) from users;"}
   temp={k:await postgres_object.fetch_all(query=v,values={}) for k,v in query_dict.items()}
   response={"status":1,"message":temp}
   #final
   return response

#otp send mobile sns
from fastapi import Request
from fastapi.responses import JSONResponse
from config import sns_region,sns_access_key_id,sns_secret_access_key
import boto3,random
@router.get("/otp-send-mobile-sns")
async def otp_send_mobile_sns(request:Request,mobile:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   otp=random.randint(100000,999999)
   sns_client=boto3.client("sns",region_name=sns_region,aws_access_key_id=sns_access_key_id,aws_secret_access_key=sns_secret_access_key)
   output=sns_client.publish(PhoneNumber=mobile,Message=f"otp={otp}")
   query="insert into otp (otp,mobile) values (:otp,:mobile) returning *;"
   query_param={"otp":otp,"mobile":mobile}
   await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#otp send email ses
from fastapi import Request
from fastapi.responses import JSONResponse
from config import ses_region,ses_access_key_id,ses_secret_access_key,ses_email
import boto3,random
@router.get("/otp-send-email-ses")
async def otp_send_email_ses(request:Request,email:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   otp=random.randint(100000,999999)
   ses_client=boto3.client("ses",region_name=ses_region,aws_access_key_id=ses_access_key_id,aws_secret_access_key=ses_secret_access_key)
   output=ses_client.send_email(Source=ses_email,Destination={"ToAddresses":[email]},Message={"Subject":{"Charset":"UTF-8","Data":"otp"},"Body":{"Text":{"Charset":"UTF-8","Data":str(otp)}}})
   query="insert into otp (otp,email) values (:otp,:email) returning *;"
   query_param={"otp":otp,"email":email}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":"otp sent"}

#otp verify email
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
@router.get("/otp-verify-email")
async def ot_verify_email(request:Request,otp:int,email:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#otp verify mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import postgtes_otp_verify
@router.get("/otp-verify-mobile")
async def ot_verify_mobile(request:Request,otp:int,mobile:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#s3 upload file
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from config import s3_region,s3_access_key_id,s3_secret_access_key,s3_bucket_name
from fastapi import UploadFile
import boto3,uuid
@router.get("/s3-upload-file")
async def s3_upload-file(request:Request,file:UploadFile):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   key=str(uuid.uuid4())+"-"+file.filename
   s3_client=boto3.client("s3",region_name=s3_region,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_client.upload_file(file,s3_bucket_name,NAME_FOR_S3)
   #final
   return {"status":1,"message":output}

#s3 create url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from config import s3_region,s3_access_key_id,s3_secret_access_key,s3_bucket_name
import boto3,uuid
@router.get("/s3-create-url")
async def s3_create_url(request:Request,filename:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   key=str(uuid.uuid4())+"-"+filename
   s3_client=boto3.client("s3",region_name=s3_region,aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_client.generate_presigned_post(Bucket=s3_bucket_name,Key=key,ExpiresIn=60,Conditions=[['content-length-range',1,250*1024]])
   #final
   return {"status":1,"message":output}

#s3 delete url
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from config import s3_region,s3_access_key_id,s3_secret_access_key,s3_bucket_name
import boto3
@router.delete("/s3-delete-url")
async def s3_delete_url(request:Request,url:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   key=url.rsplit("/",1)[1]
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Object(s3_region,key).delete()
   #final
   return {"status":1,"message":output}

#s3 delete all
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from config import s3_region,s3_access_key_id,s3_secret_access_key,s3_bucket_name
import boto3
@router.delete("/s3-delete-all")
async def s3_delete_all(request:Request):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   s3_resource=boto3.resource("s3",aws_access_key_id=s3_access_key_id,aws_secret_access_key=s3_secret_access_key)
   output=s3_resource.Bucket(s3_bucket_name).objects.all().delete()
   #final
   return {"status":1,"message":output}

#message received
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import BackgroundTasks
from datetime import datetime
from function import postgres_object_update
@router.get("/message-received")
async def message_received(request:Request,background:BackgroundTasks,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and parent_id=:parent_id order by {order} limit {limit} offset {(page-1)*limit};"
   if mode=="unread":query=f"select * from message where parent_table='users' and parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background
   object_list=[{"id":item["id"],"status":"read","updated_by_id":user["id"]} for item in output]
   response=await postgres_object_update(postgres_object,column_datatype,"background","message",object_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return {"status":1,"message":output}

#message inbox
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.get("/message-inbox")
async def message_inbox(request:Request,order:str="id desc",limit:int=100,page:int=1,mode:str=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit {limit} offset {(page-1)*limit}),y as (select m.* from x left join message as m on x.id=m.id) select * from y order by {order};"
   if mode=="unread":query=f"with mcr as (select id,abs(created_by_id-parent_id) as unique_id from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select m.* from x left join message as m on x.id=m.id) select * from y where parent_id=:parent_id and status is null order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#message thread
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from fastapi import BackgroundTasks
from datetime import datetime
@router.get("/message-thread")
async def message_thread(request:Request,background:BackgroundTasks,user_id:int,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   query=f"select * from message where parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by {order} limit {limit} offset {(page-1)*limit};"
   query_param={"user_1":user["id"],"user_2":user_id}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #background
   query="update message set status=:status,updated_at=:updated_at,updated_by_id=:updated_by_id where parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
   query_param={"status":"read","updated_at":datetime.now(),"updated_by_id":user['id'],"created_by_id":user_id,"parent_id":user["id"]}
   background.add_task(await postgres_object.fetch_all(query=query,values=query_param))
   #final
   return {"status":1,"message":output}

#message delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.delete("/message-delete")
async def message_delete(request:Request,mode:str,id:int=None):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if mode=="created":
     query="delete from message where parent_table='users' and created_by_id=:created_by_id;"
     query_param={"created_by_id":user["id"]}
   if mode=="received":
     query="delete from message where parent_table='users' and parent_id=:parent_id;"
     query_param={"parent_id":user["id"]}
   if mode=="all":
     query="delete from message where parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
     query_param={"created_by_id":user["id"],"parent_id":user["id"]}
   if mode=="single":
     if not id:return JSONResponse(status_code=400,content={"status":0,"message":"id must"})
     query="delete from message where parent_table='users' and id=:id and (created_by_id=:created_by_id or parent_id=:parent_id);"
     query_param={"id":id,"created_by_id":user["id"],"parent_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#parent read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_parent_read
@router.get("/parent-read")
async def parent_read(request:Request,table:str,parent_table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await postgres_parent_read(postgres_object,table,parent_table,order,limit,(page-1)*limit,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#parent check
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_parent_check
@router.get("/parent-check")
async def parent_check(request:Request,table:str,parent_table:str,parent_ids:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   response=await postgres_parent_check(postgres_object,table,parent_table,parent_ids,user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#location
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_location_search
from function import where_clause
@router.get("/location-search")
async def location_search(request:Request,table:str,location:str,within:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   response=await postgres_location_search(postgres_object,table,location,within,order,limit,(page-1)*limit,where_string,where_value)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#update email
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgtes_otp_verify
from function import postgres_object_update
@router.put("/update-email")
async def update_email(request:Request,otp:int,email:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic      
   response=await postgtes_otp_verify(postgres_object,otp,email,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object={"id":user["id"],"updated_by_id":user["id"],"email":email}
   response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#update mobile
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgtes_otp_verify
from function import postgres_object_update
@router.put("/update-mobile")
async def update_mobile(request:Request,otp:int,mobile:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic      
   response=await postgtes_otp_verify(postgres_object,otp,None,mobile)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   object={"id":user["id"],"updated_by_id":user["id"],"mobile":mobile}
   response=await postgres_object_update(postgres_object,column_datatype,"normal","users",[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#delete ids
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
@router.delete("/delete-ids")
async def delete_ids(request:Request,table:str,ids:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth check
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic      
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   if len(ids.split(","))>3:return JSONResponse(status_code=400,content={"status":0,"message":"ids length not allowed"})
   query=f"delete from {table} where created_by_id=:created_by_id and id in ({ids});"
   query_param={"created_by_id":user["id"]}
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#object create
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_create
@router.post("/object-create")
async def object_create(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","users","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["created_by_id"]=user["id"]
   for item in ["id","created_at","updated_at","updated_by_id","is_active","is_verified","is_protected","password","google_id","otp"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_create(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object update
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_update
from function import postgres_object_ownership_check
@router.put("/object-update")
async def object_update(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","otp","log","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["updated_by_id"]=user["id"]
   response=await postgres_object_ownership_check(postgres_object,table,object["id"],user["id"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   for item in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]:
      if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   if table=="users":
      for item in ["email","mobile"]:
         if item in object:return JSONResponse(status_code=400,content={"status":0,"message":f"{item} not allowed"})
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object update admin
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import postgres_object_update
@router.put("/object-update-admin")
async def object_update_admin(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["spatial_ref_sys","otp","log"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   object=await request.json()
   if not object:return JSONResponse(status_code=400,content={"status":0,"message":"body is must"})
   object["updated_by_id"]=user["id"]
   response=await postgres_object_update(postgres_object,column_datatype,"normal",table,[object])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object delete
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.delete("/object-delete")
async def object_delete(request:Request,table:str):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   if table in ["users"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   param=dict(request.query_params)|{"created_by_id":f"=,{user['id']}"}
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"delete from {table} {where_string};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#object read
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/object-read")
async def object_read(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   param["created_by_id"]=f"=,{user['id']}"
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   #final
   return {"status":1,"message":output}

#object read public
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
from fastapi_cache.decorator import cache
from function import redis_key_builder
from function import postgres_add_creator_key
from function import postgres_add_action_count
@router.get("/object-read-public")
@cache(expire=60,key_builder=redis_key_builder)
async def object_read_public(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #logic
   if table not in ["users","post","atom","box"]:return JSONResponse(status_code=400,content={"status":0,"message":"table not allowed"})
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response=await postgres_add_creator_key(postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   output=response["message"]
   response=await postgres_add_action_count(postgres_object,"likes",table,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   #final
   return response

#object read private
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/object-read-private")
async def object_read_private(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,None,None,None)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response

#object read admin
from fastapi import Request
from fastapi.responses import JSONResponse
from function import auth_check
from config import jwt_secret_key
from function import where_clause
@router.get("/object-read-admin")
async def object_read_admin(request:Request,table:str,order:str="id desc",limit:int=100,page:int=1):
   #middleware
   postgres_object=request.state.postgres_object
   column_datatype=request.state.column_datatype
   #auth
   response=await auth_check(request,jwt_secret_key,postgres_object,1,["admin"])
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   user=response["message"]
   #logic
   param=dict(request.query_params)
   response=await where_clause(param,column_datatype)
   if response["status"]==0:return JSONResponse(status_code=400,content=response)
   where_string,where_value=response["message"][0],response["message"][1]
   query=f"select * from {table} {where_string} order by {order} limit {limit} offset {(page-1)*limit};"
   query_param=where_value
   output=await postgres_object.fetch_all(query=query,values=query_param)
   response={"status":1,"message":output}
   #final
   return response
