from fastapi import Request,Response
def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])

async def function_read_constraint_name_list(postgres_object):
  query="select constraint_name from information_schema.constraint_column_usage;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  schema_constraint_name_list=[item["constraint_name"] for item in output]
  return {"status":1,"message":schema_constraint_name_list}

async def function_delete_index_all(postgres_object):
  query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  if output[0]["output"]:
    query=output[0]["output"]
    values={}
    try:output=await postgres_object.fetch_all(query=query,values=values)
    except Exception as e:return {"status":0,"message":e.args}
  return None









   
      
      
      

  
    

  

  
  

