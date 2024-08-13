from fastapi import Request,Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[repr(sorted(request.query_params.items())),namespace,request.method.lower(),request.url.path]
  return ":".join(param)

async def function_verify_otp(postgres_object,otp,email,mobile):
  try:
    if email and mobile:return {"status":0,"message":"wrong param"}
    if email:
      query="select otp from otp where email=:email order by id desc limit 1;"
      values={"email":email}
    if mobile:
      query="select otp from otp where mobile=:mobile order by id desc limit 1;"
      values={"mobile":mobile}
    output=await postgres_object.fetch_all(query=query,values=values)
    if not output:return {"status":0,"message":"otp not exist"}
    if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatched"}
  except Exception as e:return {"status":0,"message":e.args}
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
#principle=select * from :table :where :olo;
#wont work for in operator
from datetime import datetime
async def function_read_object(postgres_object,body):
  try:
    #query set
    table=body["table"]
    order=body["order"] if "order" in body else "id desc"
    limit=int(body["limit"]) if "limit" in body else 30
    page=int(body["page"]) if "page" in body else 1
    offset=(page-1)*limit
    where_dict={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
    key_joined=' and'.join([f"({k} {body[f'{k}_operator']} :{k} or :{k} is null)" if f"{k}_operator" in body else f"({k} = :{k} or :{k} is null)" for k,v in where_dict.items()])
    where=f"where {key_joined}" if key_joined else ""
    #column datatype
    query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
    values={}
    output=await postgres_object.fetch_all(query=query,values=values)
    column_datatype={item["column_name"]:item["datatype"] for item in output}
    #santized where
    for k,v in where_dict.items():
      if column_datatype[k] in ["ARRAY"]:where_dict[k]=v.split(",")
      if column_datatype[k] in ["integer","bigint"]:where_dict[k]=int(v)
      if column_datatype[k] in ["decimal","numeric","real","double precision"]:where_dict[k]=float(v)
      if column_datatype[k] in ["date","timestamp with time zone"]:where_dict[k]=datetime.strptime(v,'%Y-%m-%d')
    #query run
    query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
    values=where_dict
    output=await postgres_object.fetch_all(query=query,values=values)
    output=[dict(item) for item in output]
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":output}
