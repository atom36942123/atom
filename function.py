def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])

async def function_read_constraint_name_list(postgres_object):
  query="select constraint_name from information_schema.constraint_column_usage;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  schema_constraint_name_list=[item["constraint_name"] for item in output]
  return {"status":1,"message":schema_constraint_name_list}
  
    

  

  
  

