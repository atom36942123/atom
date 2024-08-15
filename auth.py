#router
from fastapi import APIRouter
router=APIRouter(tags=["auth"])

#api
# from fastapi import Request
# import hashlib
# @router.post("/{x}/auth/signup")
# async def function_auth_signup(request:Request):
#    #prework
#    body=await request.json()
#    #logic
#    query="insert into users (username,password) values (:username,:password) returning *;"
#    values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return {"status":1,"message":output}

# from config import config_key_jwt
# from fastapi import Request
# import hashlib,json,jwt,time
# from datetime import datetime
# from datetime import timedelta
# @router.post("/{x}/auth/login")
# async def function_auth_login(request:Request):
#    #prework
#    body=await request.json()
#    #read user
#    query="select * from users where username=:username and password=:password order by id desc limit 1;"
#    values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    user=output[0] if output else None
#    if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
#    #token encode
#    user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
#    data=json.dumps(user,default=str)
#    payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
#    token=jwt.encode(payload,config_key_jwt)
#    #final
#    return {"status":1,"message":token}

# from config import config_key_jwt
# from fastapi import Request
# import hashlib,json,jwt,time
# from datetime import datetime
# from datetime import timedelta
# @router.post("/{x}/auth/google")
# async def function_auth_google(request:Request,google_id:str):
#    #read user
#    query="select * from users where google_id=:google_id order by id desc limit 1;"
#    values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    user=output[0] if output else None
#    #create user
#    if not user:
#       query="insert into users (google_id) values (:google_id) returning *;"
#       values={"google_id":hashlib.sha256(google_id.encode()).hexdigest()}
#       output=await request.state.postgres_object.fetch_all(query=query,values=values)
#       user_id=output[0]["id"]
#       query="select * from users where id=:id;"
#       values={"id":user_id}
#       output=await request.state.postgres_object.fetch_all(query=query,values=values)
#       user=output[0]
#    #token encode
#    user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"x":str(request.url.path).split("/")[1],"id":user["id"],"is_active":user["is_active"],"type":user["type"]}
#    data=json.dumps(user,default=str)
#    payload={"exp":time.mktime((datetime.now()+timedelta(days=100000)).timetuple()),"data":data}
#    token=jwt.encode(payload,config_key_jwt)
#    #final
#    return {"status":1,"message":token}

from config import config_key_jwt
from fastapi import Request
import json,jwt,time
from datetime import datetime
from datetime import timedelta
@router.post("/{x}/auth/email")
async def function_auth_email(request:Request,email:str,otp:int):
   #verify otp
   


   
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
         
  
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body["email"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (email) values (:email) returning *;"
         values={"email":body["email"]}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user=output[0]
   #body={"mode":"mobile","mobile":"xxx","otp":123}
   if "mode" in body and body["mode"]=="mobile":
      response=await function_verify_otp(request.state.postgres_object,body["otp"],None,body["mobile"])
      if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body["mobile"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body["mobile"]}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
         user=output[0]
   #body={"mode":"token_refresh"}
   if "mode" in body and body["mode"]=="token_refresh":
      user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
      if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
      query="select * from users where id=:id;"
      values={"id":user["id"]}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
  
  
