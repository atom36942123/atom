#router
from fastapi import APIRouter
router=APIRouter(tags=["database"])

#query runner
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/query-runner")
async def function_database_query_runner(request:Request,query:str):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #logic
   query=query
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return output

#database clean
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/clean")
async def function_database_clean(request:Request):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #creator null
   for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #parent null
   for table in ["likes","bookmark","report","block","rating","comment","message"]:
      for parent_table in ["users","post","comment"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         values={}
         output=await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
   
#database init
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
@router.get("/{x}/database/init")
async def function_database_init(request:Request):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #constraint name list
   query="select constraint_name from information_schema.constraint_column_usage;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   constraint_name_list=[item["constraint_name"] for item in output]
   #table
   config_database_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp"]
   for table in config_database_table:
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      await request.state.postgres_object.fetch_all(query=query,values=values)
   #column
   config_database_column={
   "created_at":["timestamptz",config_database_table],
   "created_by_id":["bigint",config_database_table],
   "updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
   "updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
   "is_active":["int",["users","post"]],
   "is_verified":["int",["users","post"]],
   "is_protected":["int",["users","post","box","atom"]],
   "type":["text",["users","post","box","atom","helpdesk"]],
   "status":["text",["report","helpdesk","message"]],
   "remark":["text",["report","helpdesk"]],
   "metadata":["jsonb",["users","post","box","atom"]],
   "parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
   "parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
   "last_active_at":["timestamptz",["users"]],
   "google_id":["text",["users"]],
   "otp":["int",["otp"]],
   "username":["text",["users"]],
   "password":["text",["users"]],
   "name":["text",["users"]],
   "email":["text",["users","post","box","atom","otp"]],
   "mobile":["text",["users","post","box","atom","otp"]],
   "title":["text",["users","post","box","atom"]],
   "description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
   "tag":["text",["users","post","box","atom"]],
   "link":["text",["post","box","atom"]],
   "file":["text",["post","box","atom"]],
   "rating":["numeric",["rating"]],
   }
   for k,v in config_database_column.items():
      for table in v[1]:
         query=f"alter table {table} add column if not exists {k} {v[0]};"
         values={}
         await request.state.postgres_object.fetch_all(query=query,values=values)
   #created_at default
   for table in config_database_table:
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      await request.state.postgres_object.fetch_all(query=query,values=values)
   #protected rows
   for table in config_database_column["is_protected"][1]:
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      await request.state.postgres_object.fetch_all(query=query,values=values)
   #not null
   config_database_column_not_null={
   "parent_table":["likes","bookmark","report","block","rating","comment","message"],
   "parent_id":["likes","bookmark","report","block","rating","comment","message"]
   }
   for k,v in config_database_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         await request.state.postgres_object.fetch_all(query=query,values=values)
   #query
   config_database_query=[
   "alter table users add constraint constraint_unique_users unique (username);",
   "alter table likes add constraint constraint_unique_likes unique (created_by_id,parent_table,parent_id);",
   "alter table bookmark add constraint constraint_unique_bookmark unique (created_by_id,parent_table,parent_id);",
   "alter table report add constraint constraint_unique_report unique (created_by_id,parent_table,parent_id);",
   "alter table block add constraint constraint_unique_block unique (created_by_id,parent_table,parent_id);",
   ]
   for query in config_database_query:
      if query.split()[5] not in constraint_name_list:
         query=query
         values={}
         await request.state.postgres_object.fetch_all(query=query,values=values)
   #index
   config_database_index={
   "type":"btree",
   "is_verified":"btree",
   "is_active":"btree",
   "created_by_id":"btree",
   "status":"btree",
   "parent_table":"btree",
   "parent_id":"btree",
   "email":"btree",
   "password":"btree",
   "created_at":"brin"
   }
   for k,v in config_database_column.items():
      for table in v[1]:
         if k in config_database_index:
            query=f"create index if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
            values={}
            await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

#insert csv
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from fastapi import UploadFile
import csv,codecs
import hashlib,json
from datetime import datetime
@router.post("/{x}/database/insert-csv",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_database_insert_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   column_datatype={item["column_name"]:item["datatype"] for item in output}
   for index,object in enumerate(values_list):
      for k,v in object.items():
         if k in ["password","google_id"]:values_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if column_datatype[k] in ["jsonb"]:values_list[index][k]=json.dumps(v) if v else None
         if column_datatype[k] in ["ARRAY"]:values_list[index][k]=v.split(",") if v else None
         if column_datatype[k] in ["integer","bigint"]:values_list[index][k]=int(v) if v else None
         if column_datatype[k] in ["decimal","numeric","real","double precision"]:values_list[index][k]=round(float(v),3) if v else None
         if column_datatype[k] in ["date","timestamp with time zone"]:values_list[index][k]=datetime.strptime(v,'%Y-%m-%d') if v else None
   #logic
   column_to_insert_list=[*values_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

#update csv
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
from function import function_sanitization_values_list
import hashlib,json
from datetime import datetime
@router.post("/{x}/database/update-csv")
async def function_database_update_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   column_datatype={item["column_name"]:item["datatype"] for item in output}
   for index,object in enumerate(values_list):
      for k,v in object.items():
         if k in ["password","google_id"]:values_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if column_datatype[k] in ["jsonb"]:values_list[index][k]=json.dumps(v) if v else None
         if column_datatype[k] in ["ARRAY"]:values_list[index][k]=v.split(",") if v else None
         if column_datatype[k] in ["integer","bigint"]:values_list[index][k]=int(v) if v else None
         if column_datatype[k] in ["decimal","numeric","real","double precision"]:values_list[index][k]=round(float(v),3) if v else None
         if column_datatype[k] in ["date","timestamp with time zone"]:values_list[index][k]=datetime.strptime(v,'%Y-%m-%d') if v else None
   #logic
   column_to_update_list=[item for item in [*values_list[0]] if item not in ["id"]]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

#delete csv
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
@router.post("/{x}/database/delete-csv")
async def function_database_delete_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   for index,object in enumerate(values_list):
      for k,v in object.items():values_list[index][k]=int(v) if v else None
   #logic
   query=f"delete from {table} where id=:id;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

#read csv
from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
@router.post("/{x}/database/read-csv")
async def function_database_read_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #logic
   ids_to_read=','.join([str(item["id"]) for item in values_list])
   query=f"select * from {table} where id in ({ids_to_read}) order by id desc;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values={})
   #final
   await file.close()
   return {"status":1,"message":output}
