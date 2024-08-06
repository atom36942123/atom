def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])

async def function_get_constraint_name_list(database):
  
  

