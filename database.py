#router
from fastapi import APIRouter
router=APIRouter(tags=["database"])

# from config import config_key_root
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# @router.get("/{x}/database/query-runner")
# async def function_database_query_runner(request:Request,query:str):
#    #prework
#    if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
#    #logic
#    query=query
#    values={}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return output

# from config import config_key_root
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# @router.get("/{x}/database/clean")
# async def function_database_clean(request:Request):
#    #prework
#    if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
#    #creator null
#    for table in ["post","likes","bookmark","report","block","rating","comment","message"]:
#       query=f"delete from {table} where created_by_id not in (select id from users);"
#       values={}
#       output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #parent null
#    for table in ["likes","bookmark","report","block","rating","comment","message"]:
#       for parent_table in ["users","post","comment"]:
#          query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
#          values={}
#          output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return {"status":1,"message":"done"}

# from config import config_key_root,config_database_table,config_database_column,config_database_column_not_null,config_database_query,config_database_index
# from fastapi import Request
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# @router.get("/{x}/database/init")
# async def function_database_init(request:Request):
#    #prework
#    if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
#    #constraint name list
#    query="select constraint_name from information_schema.constraint_column_usage;"
#    values={}
#    output=await request.state.postgres_object.fetch_all(query=query,values=values)
#    constraint_name_list=[item["constraint_name"] for item in output]
#    #table
#    for table in config_database_table:
#       query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
#       values={}
#       await request.state.postgres_object.fetch_all(query=query,values=values)
#    #column
#    for k,v in config_database_column.items():
#       for table in v[1]:
#          query=f"alter table {table} add column if not exists {k} {v[0]};"
#          values={}
#          await request.state.postgres_object.fetch_all(query=query,values=values)
#    #created_at default
#    for table in config_database_table:
#       query=f"alter table {table} alter column created_at set default now();"
#       values={}
#       await request.state.postgres_object.fetch_all(query=query,values=values)
#    #protected rows
#    for table in config_database_column["is_protected"][1]:
#       query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
#       values={}
#       await request.state.postgres_object.fetch_all(query=query,values=values)
#    #not null
#    for k,v in config_database_column_not_null.items():
#       for table in v:
#          query=f"alter table {table} alter column {k} set not null;"
#          values={}
#          await request.state.postgres_object.fetch_all(query=query,values=values)
#    #query
#    for query in config_database_query:
#       if query.split()[5] not in constraint_name_list:
#          query=query
#          values={}
#          await request.state.postgres_object.fetch_all(query=query,values=values)
#    #index
#    for k,v in config_database_column.items():
#       for table in v[1]:
#          if k in config_database_index:
#             query=f"create index if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
#             values={}
#             await request.state.postgres_object.fetch_all(query=query,values=values)
#    #final
#    return {"status":1,"message":"done"}


from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from fastapi import UploadFile
import csv,codecs
@router.post("/{x}/database/insert-csv",dependencies=[Depends(RateLimiter(times=1,seconds=3))])
async def function_database_insert_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   response=await function_sanitization_values_list(request.state.postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   #logic
   column_to_insert_list=[*values_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

from config import config_key_root
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
import csv,codecs
@router.post("/{x}/database/update-csv")
async def function_database_update_csv(request:Request,table:str,file:UploadFile):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
   #values
   values_list=[]
   for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
   #sanitization
   response=await function_sanitization_values_list(request.state.postgres_object,values_list)
   if response["status"]==0:return JSONResponse(status_code=400,content=jsonable_encoder(response))
   values_list=response["message"]
   #logic
   column_to_update_list=[item for item in [*values_list[0]] if item not in ["id"]]
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   values=values_list
   output=await request.state.postgres_object.execute_many(query=query,values=values)
   #final
   await file.close()
   return {"status":1,"message":output}

# from fastapi import UploadFile
# import csv,codecs
# @router.post("/{x}/database/delete-csv")
# async def function_database_update_csv(request:Request,table:str,file:UploadFile):
#    #prework
#    if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
#    if file.content_type!="text/csv":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"file type issue"}))
#    #values
#    values_list=[]
#    for row in csv.DictReader(codecs.iterdecode(file.file,'utf-8')):values_list.append(row)
#    #sanitization
#    #logic
#    column_to_update_list=[item for item in [*values_list[0]] if item not in ["id"]]
#    query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
#    values=values_list
#    output=await request.state.postgres_object.execute_many(query=query,values=values)
#    #final
#    await file.close()
#    return {"status":1,"message":output}





    # query=f"delete from {table} where id=:id;"
    #   values=values_list
    #   output=await request.state.postgres_object.execute_many(query=query,values=values)
   
   
   
   


   # if mode=="read":
   #    ids_to_read=','.join([str(item["id"]) for item in values_list])
   #    query=f"select * from {table} where id in ({ids_to_read}) order by id desc;"
   #    values={}
   #    output=await request.state.postgres_object.fetch_all(query=query,values=values)

      
      
      
  


