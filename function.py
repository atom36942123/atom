from fastapi import Request,Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
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
  return {"status":1,"message":"done"}

async def function_read_schema_column(postgres_object):
  query="select * from information_schema.columns where table_schema='public' order by column_name;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":output}

async def function_read_schema_column_datatype(postgres_object):
  query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
  return {"status":1,"message":schema_column_datatype}

async def function_verify_otp(postgres_object,otp,email,mobile):
  if email:
    query="select otp from box where type='otp' and email=:email order by id desc limit 1;"
    values={"email":email}
  if mobile:
    query="select otp from box where type='otp' and mobile=:mobile order by id desc limit 1;"
    values={"mobile":mobile}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  if not output:return {"status":0,"message":"otp not exist"}
  if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatched"}
  return {"status":1,"message":"done"}
  
async def function_add_creator_key(postgres_object,object_list):
  if not object_list:return {"status":1,"message":object_list}
  try:
    object_list=[item|{"created_by_username":None} for item in object_list]
    user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
    if user_ids:
      query=f"select * from users where id in ({user_ids});"
      values={}
      object_user_list=await postgres_object.fetch_all(query=query,values=values)
      for x in object_list:
        for y in object_user_list:
           if x["created_by_id"]==y["id"]:
             x["created_by_username"]=y["username"]
             break
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":object_list}

async def function_add_action_count(postgres_object,object_list,object_table,action_table,action_type):
  if not object_list:return {"status":1,"message":object_list}
  try:
    key_name=f"{action_type}_count"
    object_list=[item|{key_name:0} for item in object_list]
    parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
    if parent_ids:
      query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where type=:type and parent_table=:parent_table group by parent_id;"
      values={"type":action_type,"parent_table":object_table}
      object_action_list=await postgres_object.fetch_all(query=query,values=values)
      for x in object_list:
        for y in object_action_list:
          if x["id"]==y["parent_id"]:
            x[key_name]=y["count"]
            break
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":object_list}
