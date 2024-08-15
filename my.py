#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#profile
# from config import config_key_jwt
# import jwt,json
# from fastapi import Request
# from fastapi import BackgroundTasks
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# from datetime import datetime
# @router.get("/{x}/my/profile")
# async def function_my_profile(request:Request,background:BackgroundTasks):
#    #prework
#    user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
#    if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
#    #read user
#    query="select * from users where id=:id;"
#    values={"id":user["id"]}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    user=output[0] if output else None
#    if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
#    #background
#    query="update users set last_active_at=:last_active_at where id=:id;"
#    values={"last_active_at":datetime.now(),"id":user["id"]}
#    background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
#    #final
#    return {"status":1,"message":user}

#stats
# from config import config_key_jwt
# import jwt,json
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# @router.get("/{x}/my/stats")
# async def function_my_stats(request:Request):
#    #prework
#    user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
#    if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
#    #user extra info
#    user_stats={
#    "post_count":"select count(*) from post where created_by_id=:user_id;",
#    "message_unread_count":"select count(*) from message where parent_table='users' and parent_id=:user_id and status is null;"
#    }
#    temp={}
#    for k,v in user_stats.items():
#       query=v
#       values={"user_id":user["id"]}
#       output=await request.state.postgres_object.fetch_all(query=query,values=values)
#       if "count" in k:temp[k]=output[0]["count"]
#       else:temp[k]=output
#    #final
#    return {"status":1,"message":temp}

#create object
# from config import config_key_jwt
# import jwt,json
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# @router.post("/{x}/my/create-object")
# async def function_my_create_object(request:Request,table:str):
#    #prework
#    user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
#    if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
#    if table in ["users","atom","otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
#    body=await request.json()
#    #query set
#    column_to_insert_list=[item for item in [*body] if item not in ["id","created_at","is_active","is_verified","google_id","otp"]]+["created_by_id"]
#    query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
#    #values
#    values={}
#    for item in column_to_insert_list:
#       if item in body:values[item]=body[item]
#       else:values[item]=None
#    values["created_by_id"]=user["id"]
#    if "metadata" in values:values["metadata"]=json.dumps(values["metadata"],default=str)
#    #query run
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return {"status":1,"message":output}

#update object
# from config import config_key_jwt
# import jwt,json
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# from datetime import datetime
# @router.post("/{x}/my/update-object")
# async def function_my_update_object(request:Request,table:str,id:int):
#    #prework
#    user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
#    if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
#    body=await request.json()
#    #query set
#    column_to_update_list=[item for item in [*body] if item not in ["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"]]+["updated_at","updated_by_id"]
#    query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
#    #values
#    values={}
#    for item in column_to_update_list:
#       if item in body:values[item]=body[item]
#       else:values[item]=None
#    values["updated_at"]=datetime.now()
#    values["updated_by_id"]=user["id"]
#    values["id"]=user["id"] if table=="users" else id
#    values["created_by_id"]=None if table=="users" else user["id"]
#    if "metadata" in values:values["metadata"]=json.dumps(values["metadata"],default=str)
#    #query run
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return {"status":1,"message":output}
