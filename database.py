@router.get("/{x}/database")
async def function_database(request:Request):
   #prework
   if request.headers.get("Authorization").split(" ",1)[1]!=config_key_root:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #constraint name list
   query="select constraint_name from information_schema.constraint_column_usage;"
   values={}
   output=await request.state.postgres_object.fetch_all(query=query,values=values)
   constraint_name_list=[item["constraint_name"] for item in output]
   #table
   for table in config_database_table:
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      await request.state.postgres_object.fetch_all(query=query,values=values)
   #column
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
   for k,v in config_database_column_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         await request.state.postgres_object.fetch_all(query=query,values=values)
   #query
   for query in config_database_query:
      if query.split()[5] not in constraint_name_list:
         query=query
         values={}
         await request.state.postgres_object.fetch_all(query=query,values=values)
   #index
   for k,v in config_database_column.items():
      for table in v[1]:
         if k in config_database_index:
            query=f"create index if not exists index_{k}_{table} on {table} using {config_database_index[k]} ({k});"
            values={}
            await request.state.postgres_object.fetch_all(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
