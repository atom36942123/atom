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
   #token check
   if request.headers.get("token")!=env("key"):return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #create table
   for item in config_database["created_at"][0]:await request.state.postgres_object.fetch_all(query=f"create table if not exists {item} (id bigint primary key generated always as identity);",values={})
   #create column
   for k,v in config_database.items():
      if len(v)!=5:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"config_databae length issue"}))
      for item in v[0]:await request.state.postgres_object.fetch_all(query=f"alter table {item} add column if not exists {k} {v[1]};",values={})
   #helper
   schema_column=await request.state.postgres_object.fetch_all(query="select * from information_schema.columns where table_schema='public';",values={})
   schema_constraint_name_list=[item["constraint_name"] for item in await request.state.postgres_object.fetch_all(query="select constraint_name from information_schema.constraint_column_usage;",values={})]
   #alter
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} alter column {k} set default {v[2]};",values={}) for k,v in config_database.items() for table in v[0] for column in schema_column if v[2] is not None and column["column_name"]==k and column["table_name"]==table and not column["column_default"]]
   [await request.state.postgres_object.fetch_all(query=f"alter table {table} add constraint {f'checkin_{k}_{table}'} check ({k} in {v[3]});",values={}) for k,v in config_database.items() for table in v[0] if v[3] and f'checkin_{k}_{table}' not in schema_constraint_name_list]
   [await request.state.postgres_object.fetch_all(query=item,values={}) for item in alter_query if item.split()[5] not in schema_constraint_name_list]
   #index
   output=await request.state.postgres_object.fetch_all(query='''select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;''',values={})
   if output[0]["output"]:await request.state.postgres_object.fetch_all(query=output[0]["output"],values={})
   for k,v in config_database.items():
      for table in v[0]:
         if v[4]==1:
            if v[1]=="array":await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table} using gin ({k});",values={})
            else:await request.state.postgres_object.fetch_all(query=f"create index if not exists {f'index_{k}_{table}'} on {table}({k});",values={})
   [await request.state.postgres_object.fetch_all(query=item,values={}) for item in ["create index if not exists index_parent_table_parent_id_likes on likes(parent_table,parent_id);","create index if not exists index_parent_table_parent_id_bookmark on bookmark(parent_table,parent_id);","create index if not exists index_parent_table_parent_id_comment on comment(parent_table,parent_id);"]]
   #final response
   return {"status":1,"message":"done"}


      

      
   




    
    
    
    
     




                   

    


   
   
