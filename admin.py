#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])

#update cell
@router.post("/{x}/admin/update-cell")
async def function_admin_update_cell(request:Request):
   #prework
   user=json.loads(jwt.decode(request.headers.get("Authorization").split(" ",1)[1],config_key_jwt,algorithms="HS256")["data"])
   if user["x"]!=str(request.url.path).split("/")[1]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   body=dict(await request.json())
   #logic
   #body={"mode":"update_cell","table":"users","id":12,"column":"name","value":"xxx"}
   if body["mode"]=="update_cell":
      if body["column"] in ["password","google_id"]:body["value"]=hashlib.sha256(body["value"].encode()).hexdigest()
      if body["column"] in ["metadata"]:body["value"]=json.dumps(body["value"])
      query=f"update {body['table']} set {body['column']}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
      values={"value":body["value"],"id":body["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":output}

