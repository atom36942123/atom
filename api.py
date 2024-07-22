#router
from fastapi import APIRouter
router=APIRouter()

#helper
from helper import *

#api
@router.get("/{x}/query-runner")
async def function_query_runner(request:Request,query:str):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   return {"status":1,"message":await request.state.postgres_object.fetch_all(query=query,values={})}

@router.post("/{x}/insert-csv")
async def function_insert_csv(request:Request,table:str,file:UploadFile):
   #check
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"only csv allowed"}))
   if file.size>=100000:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file size should be<=100000 bytes"}))
   #logic
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   if set(file_object.fieldnames)!=set(["created_by_id","type","title","description","file_url","link_url","tag"]):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"csv column mismatch-ct2t"}))
   values=[]
   for row in file_object:
      row["created_by_id"]=int(row["created_by_id"]) if row["created_by_id"] else None
      row["tag"]=row["tag"].split(",") if row["tag"] else None
      values.append(row)
   file.file.close   
   return {"status":1,"message":await request.state.postgres_object.execute_many(query=f"insert into {table} (created_by_id,type,title,description,file_url,link_url,tag) values (:created_by_id,:type,:title,:description,:file_url,:link_url,:tag) returning *;",values=values)}

@router.get("/{x}/database-init")
async def function_database_init(request:Request):
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   for k,v in config_database.items():
      for table in v[0]:
         if k=="created_at":await request.state.postgres_object.fetch_all(query=f"create table if not exists {table} (id bigint primary key generated always as identity);",values={})
         if k not in ["alter_query"] and len(v)!=5:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":f"config_databae length issue {k}"}))
         if k not in ["alter_query"]:await request.state.postgres_object.fetch_all(query=f"alter table {table} add column if not exists {k} {v[1]};",values={})
         if k not in ["alter_query"] and v[2] is not None:await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column {k} set default {v[2]};",values={})
         if k not in ["alter_query"] and v[3] is not None and f'checkin_{k}_{table}' not in schema_constraint_name_list:await request.state.postgres_object.fetch_all(query=f"alter table {table} add constraint {f'checkin_{k}_{table}'} check ({k} in {v[3]});",values={})
         if k not in ["alter_query"] and v[4]==1 and v[1]=="array":await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table} using gin ({k});",values={})
         if k not in ["alter_query"] and v[4]==1 and v[1] not in ["array"]:await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table}({k});",values={})
         if k in ["alter_query"]:[await request.state.postgres_object.fetch_all(query=item,values={}) for item in alter_query if item.split()[5] not in schema_constraint_name_list]
            return (8)
   return {"status":1,"message":"done"}

# @router.get("/{x}/metric")
# async def function_metric(request:Request,query:str):
#    if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
#    return {"status":1,"message":await request.state.postgres_object.fetch_all(query=query,values={})}

@router.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=1))])
async def function_signup(request:Request):
   body=await request.json()
   if not body["username"] or not body["password"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"body issue"}))
   return {"status":1,"message":await request.state.postgres_object.fetch_all(query="insert into users (username,password) values (:username,:password) returning *;",values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()})}
   


      

      
   




    
    
    
    
     




                   

    


   
   
