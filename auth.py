#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#singup
from fastapi import Request
import hashlib
@router.post("/{x}/auth/signup")
async def function_auth_signup(request:Request,username:str,password:str):
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

#login
from config import config_key_jwt
import hashlib
from fastapi import Request
@router.get("/{x}/auth/login")
async def function_auth_login(request:Request,username:str,password:str):
   #read user
   query="select * from users where username=:username and password=:password order by id desc limit 1;"
   values={"username":username,"password":hashlib.sha256(password.encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #token encode
   response=await function_add_creator_key(request.state.postgres_object,output)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   output=response["message"]
   #final
   return {"status":1,"message":token}

#login google
from config import config_key_jwt
import jwt,time,json
from datetime import datetime
from datetime import timedelta
import hashlib
from fastapi import Request
@router.post("/{x}/auth/google")
async def function_auth_google(request:Request,google_id:str):
   #read user
   query="select * from users where google_id=:google_id order by id desc limit 1;"
   values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (google_id) values (:google_id) returning *;"
      values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #token encode
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   data=json.dumps(user,default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}

#login email
from config import config_key_jwt
import jwt,time,json
from datetime import datetime
from datetime import timedelta
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/email")
async def function_auth_email(request:Request,email:str,otp:int):
   #verify otp
   query="select otp from otp where email=:email order by id desc limit 1;"
   values={"email":email}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
   #read user
   query="select * from users where email=:email order by id desc limit 1;"
   values={"email":email}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (email) values (:email) returning *;"
      values={"email":email}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #token encode
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   data=json.dumps(user,default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}

#login mobile
from config import config_key_jwt
import jwt,time,json
from datetime import datetime
from datetime import timedelta
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.post("/{x}/auth/mobile")
async def function_auth_mobile(request:Request,mobile:str,otp:int):
   #verify otp
   query="select otp from otp where mobile=:mobile order by id desc limit 1;"
   values={"mobile":mobile}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
   if int(output[0]["otp"])!=int(otp):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatch"}))
   #read user
   query="select * from users where mobile=:mobile order by id desc limit 1;"
   values={"mobile":mobile}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   #create user
   if not user:
      query="insert into users (mobile) values (:mobile) returning *;"
      values={"mobile":mobile}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user_id=output[0]["id"]
      query="select * from users where id=:id;"
      values={"id":user_id}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0]
   #token encode
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   data=json.dumps(user,default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}

#refresh
from config import config_key_jwt
import jwt,time,json
from datetime import datetime
from datetime import timedelta
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/auth/refresh")
async def function_auth_refresh(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #token encode
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
   data=json.dumps(user,default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
   token=jwt.encode(payload,config_key_jwt)
   #final
   return {"status":1,"message":token}
