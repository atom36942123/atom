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

async def function_read_column_datatype(postgres_object):
  query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
  values={}
  try:output=await postgres_object.fetch_all(query=query,values=values)
  except Exception as e:return {"status":0,"message":e.args}
  schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
  return {"status":1,"message":schema_column_datatype}

async def function_verify_otp(postgres_object,otp,email,mobile):
  if email and mobile:return {"status":0,"message":"wrong param"}
  if email:
    query="select otp from otp where email=:email order by id desc limit 1;"
    values={"email":email}
  if mobile:
    query="select otp from otp where mobile=:mobile order by id desc limit 1;"
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

async def function_add_action_count(postgres_object,object_list,object_table,action_table):
  if not object_list:return {"status":1,"message":object_list}
  try:
    key_name=f"{action_table}_count"
    object_list=[item|{key_name:0} for item in object_list]
    parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
    if parent_ids:
      query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
      values={"parent_table":object_table}
      object_action_list=await postgres_object.fetch_all(query=query,values=values)
      for x in object_list:
        for y in object_action_list:
          if x["id"]==y["parent_id"]:
            x[key_name]=y["count"]
            break
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":object_list}

#body min={"table":"post"}
#body max={"table":"post","order":"id desc","limit":100,"page":100,"id":100,"id_operator":">="}
from datetime import datetime
async def function_read_object(postgres_object,body,function_read_schema_column_datatype):
  try:
    #set param=select * from :table :where :olo;
    table=body["table"]
    order=body["order"] if "order" in body else "id desc"
    limit=int(body["limit"]) if "limit" in body else 30
    page=int(body["page"]) if "page" in body else 1
    offset=(page-1)*limit
    where_dict={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
    key_joined=' and'.join([f"({k}{body[f'{k}_operator']}:{k} or :{k} is null)" if f"{k}_operator" in body else f"({k}=:{k} or :{k} is null)" for k,v in where_dict.items()])
    where=f"where {key_joined}" if key_joined else ""
    #santized filter values
    response=await function_read_schema_column_datatype(postgres_object)
    if response["status"]==0:return response
    schema_column_datatype=response["message"]
    for k,v in where_dict.items():
      datatype=schema_column_datatype[k]
      if datatype in ["ARRAY"]:where_dict[k]=v.split(",")
      if datatype in ["integer","bigint"]:where_dict[k]=int(v)
      if datatype in ["decimal","numeric","real","double precision"]:where_dict[k]=float(v)
      if datatype in ["date","timestamp with time zone"]:where_dict[k]=datetime.strptime(v,'%Y-%m-%d')
    #query run
    query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
    values=where_dict
    output=await postgres_object.fetch_all(query=query,values=values)
    output=[dict(item) for item in output]
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":output}

