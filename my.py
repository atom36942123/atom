#router
from fastapi import APIRouter
router=APIRouter(tags=["my"])

#profile
from config import config_key_jwt
from fastapi import Request
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import jwt,json
@router.get("/{x}/my/profile")
async def function_my_profile(request:Request,background:BackgroundTasks):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #background
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
   #final
   return {"status":1,"message":user}

# #stats
# @router.get("/{x}/my/stats")
# async def function_my_stats(request:Request,background:BackgroundTasks):
#    #prework
#    user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
#    if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
#    #user extra info
#    user_extra_info={
#    "post_count":"select count(*) from post where created_by_id=:user_id;",
#    "message_unread_count":"select count(*) from message where parent_table='users' and parent_id=:user_id and status is null;"
#    }
#    temp={}
#    for k,v in user_extra_info.items():
#       query=v
#       values={"user_id":user["id"]}
#       output=await request.state.postgres_object.fetch_all(query=query,values=values)
#       if "count" in k:temp[k]=output[0]["count"]
#       else:temp[k]=output
#    #background
#    query="update users set last_active_at=:last_active_at where id=:id;"
#    values={"last_active_at":datetime.now(),"id":user["id"]}
#    background.add_task(await request.state.postgres_object.fetch_all(query=query,values=values))
#    #final
#    return {"status":1,"message":user|temp}
