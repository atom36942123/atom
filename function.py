#sanitization
import hashlib,json
from datetime import datetime
async def function_sanitization_values_list(postgres_object,values_list):
  try:
    query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
    values={}
    output=await postgres_object.fetch_all(query=query,values=values)
    column_datatype={item["column_name"]:item["datatype"] for item in output}
    for index,object in enumerate(values_list):
      for k,v in object.items():
        if k in ["password","google_id"]:values_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
        if column_datatype[k] in ["jsonb"]:values_list[index][k]=json.dumps(v) if v else None
        if column_datatype[k] in ["ARRAY"]:values_list[index][k]=v.split(",") if v else None
        if column_datatype[k] in ["integer","bigint"]:values_list[index][k]=int(v) if v else None
        if column_datatype[k] in ["decimal","numeric","real","double precision"]:values_list[index][k]=round(float(v),3) if v else None
        if column_datatype[k] in ["date","timestamp with time zone"]:values_list[index][k]=datetime.strptime(v,'%Y-%m-%d') if v else None
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":values_list}

#key builder
from fastapi import Request,Response
def function_read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
  param=[repr(sorted(request.query_params.items())),namespace,request.method.lower(),request.url.path]
  return ":".join(param)

#add creator key
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

#add action count
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

#read object
from datetime import datetime
async def function_read_object(postgres_object,table,where,order,limit,offset):
  try:
    #query set
    where_dict={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
    key_joined=' and'.join([f"({k} {body[f'{k}_operator']} :{k} or :{k} is null)" if f"{k}_operator" in body else f"({k} = :{k} or :{k} is null)" for k,v in where_dict.items()])
    where=f"where {key_joined}" if key_joined else ""
    #sanitization
    query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
    values={}
    output=await postgres_object.fetch_all(query=query,values=values)
    column_datatype={item["column_name"]:item["datatype"] for item in output}
    for k,v in where_dict.items():
      if column_datatype[k] in ["ARRAY"]:where_dict[k]=v.split(",")
      if column_datatype[k] in ["integer","bigint"]:where_dict[k]=int(v)
      if column_datatype[k] in ["decimal","numeric","real","double precision"]:where_dict[k]=float(v)
      if column_datatype[k] in ["date","timestamp with time zone"]:where_dict[k]=datetime.strptime(v,'%Y-%m-%d')
  except Exception as e:return {"status":0,"message":e.args}
  return {"status":1,"message":output}
