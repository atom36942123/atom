#read redis key
from fastapi import Request,Response
def read_redis_key(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
   param=[request.method.lower(),request.url.path,namespace,repr(sorted(request.query_params.items()))]
   param=":".join(param)
   return param

#verify otp
from datetime import datetime,timezone
async def verify_otp(mode,postgres_client,otp,contact):
   if mode=="email":query="select * from otp where email=:contact order by id desc limit 1;"
   if mode=="mobile":query="select * from otp where mobile=:contact order by id desc limit 1;"
   query_param={"contact":contact}
   output=await postgres_client.fetch_all(query=query,values=query_param)
   if not output:return {"status":0,"message":"otp not found"}
   if int(datetime.now(timezone.utc).strftime('%s'))-int(output[0]["created_at"].strftime('%s'))>60:return {"status":0,"message":"otp expired"}
   if int(output[0]["otp"])!=int(otp):return {"status":0,"message":"otp mismatch"}
   return {"status":1,"message":"done"}

#create token
import jwt,json,time
from datetime import datetime,timedelta
async def create_token(secret_key_jwt,user):
   user={"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"],"is_protected":user["is_protected"]}
   expiry_time=time.mktime((datetime.now()+timedelta(days=36500)).timetuple())
   payload={"exp":expiry_time,"data":json.dumps(user,default=str)}
   token=jwt.encode(payload,secret_key_jwt)
   return {"status":1,"message":token}

#add creator key
async def add_creator_key(postgres_client,object_list):
  if not object_list:return {"status":1,"message":object_list}
  object_list=[dict(item)|{"created_by_username":None} for item in object_list]
  user_ids=','.join([str(item["created_by_id"]) for item in object_list if "created_by_id" in item and item["created_by_id"]])
  if user_ids:
    query=f"select * from users where id in ({user_ids});"
    query_param={}
    object_user_list=await postgres_client.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_user_list:
         if x["created_by_id"]==y["id"]:
           x["created_by_username"]=y["username"]
           break
  return {"status":1,"message":object_list}

#add action count
async def add_action_count(postgres_client,action,object_table,object_list):
  if not object_list:return {"status":1,"message":object_list}
  key_name=f"{action}_count"
  object_list=[dict(item)|{key_name:0} for item in object_list]
  parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
  if parent_ids:
    query=f"select parent_id,count(*) from {action} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table group by parent_id;"
    query_param={"parent_table":object_table}
    object_action_list=await postgres_client.fetch_all(query=query,values=query_param)
    for x in object_list:
      for y in object_action_list:
        if x["id"]==y["parent_id"]:
          x[key_name]=y["count"]
          break
  return {"status":1,"message":object_list}

#read where clause
import hashlib
from datetime import datetime
async def read_where_clause(postgres_schema_column_data_type,param):
   param={k:v for k,v in param.items() if k not in ["table","order","limit","page"]}
   param={k:v for k,v in param.items() if k not in ["location","metadata"]}
   param={k:v for k,v in param.items() if k in postgres_schema_column_data_type}
   where_key_value={k:v.split(',',1)[1] for k,v in param.items()}
   where_key_operator={k:v.split(',',1)[0] for k,v in param.items()}
   key_list=[f"({k} {where_key_operator[k]} :{k} or :{k} is null)" for k,v in where_key_value.items()]
   key_joined=' and '.join(key_list)
   where_string=f"where {key_joined}" if key_joined else ""
   for k,v in where_key_value.items():
      if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
      else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
      if k in ["password","google_id"]:where_key_value[k]=hashlib.sha256(v.encode()).hexdigest() if v else None
      if "int" in datatype:where_key_value[k]=int(v) if v else None
      if datatype in ["numeric"]:where_key_value[k]=round(float(v),3) if v else None
      if "time" in datatype:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["date"]:where_key_value[k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
      if datatype in ["ARRAY"]:where_key_value[k]=v.split(",") if v else None
   return {"status":1,"message":[where_string,where_key_value]}

#search postgres location 
async def search_postgres_location(postgres_client,table,location,within,order,limit,offset,where_string,where_value):
  long,lat=float(location.split(",")[0]),float(location.split(",")[1])
  min_meter,max_meter=int(within.split(",")[0]),int(within.split(",")[1])
  query=f'''
  with
  x as (select * from {table} {where_string}),
  y as (select *,st_distance(location,st_point({long},{lat})::geography) as distance_meter from x)
  select * from y where distance_meter between {min_meter} and {max_meter} order by {order} limit {limit} offset {offset};
  '''
  output=await postgres_client.fetch_all(query=query,values=where_value)
  return {"status":1,"message":output}

#create postgres object
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def create_postgres_object(postgres_client,postgres_schema_column_data_type,mode,table,object_list):
   if not object_list:return {"status":0,"message":"object list empty"}
   if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
   column_to_insert_list=[*object_list[0]]
   query=f"insert into {table} ({','.join(column_to_insert_list)}) values ({','.join([':'+item for item in column_to_insert_list])}) returning *;"
   for index,object in enumerate(object_list):
      for k,v in object.items():
         if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
         else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
         if not v:object_list[index][k]=None
         if k in ["password","google_id"]:object_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if "int" in datatype:object_list[index][k]=int(v) if v else None
         if datatype in ["numeric"]:object_list[index][k]=round(float(v),3) if v else None
         if "time" in datatype:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["date"]:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["jsonb"]:object_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:object_list[index][k]=v.split(",") if v else None
   background=BackgroundTasks()
   output=f"{len(object_list)} object created"
   if mode=="background":
      if len(object_list)==1:background.add_task(await postgres_client.fetch_all(query=query,values=object_list[0]))
      else:background.add_task(await postgres_client.execute_many(query=query,values=object_list))
   else:
      if len(object_list)==1:output=await postgres_client.fetch_all(query=query,values=object_list[0])
      else:output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}

#update postgres object
import hashlib,json
from datetime import datetime
from fastapi import BackgroundTasks
async def update_postgres_object(postgres_client,postgres_schema_column_data_type,mode,table,object_list):
   if not object_list:return {"status":0,"message":"object list empty"}
   if table in ["spatial_ref_sys"]:return {"status":0,"message":"table not allowed"}
   column_to_update_list=[*object_list[0]]
   column_to_update_list.remove("id")
   query=f"update {table} set {','.join([f'{item}=coalesce(:{item},{item})' for item in column_to_update_list])} where id=:id returning *;"
   for index,object in enumerate(object_list):
      for k,v in object.items():
         if k in postgres_schema_column_data_type:datatype=postgres_schema_column_data_type[k]
         else:return {"status":0,"message":f"{k} column not in postgres_schema_column_data_type"}
         if not v:object_list[index][k]=None
         if k in ["password","google_id"]:object_list[index][k]=hashlib.sha256(v.encode()).hexdigest() if v else None
         if "int" in datatype:object_list[index][k]=int(v) if v else None
         if datatype in ["numeric"]:object_list[index][k]=round(float(v),3) if v else None
         if "time" in datatype:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["date"]:object_list[index][k]=datetime.strptime(v,'%Y-%m-%dT%H:%M:%S') if v else None
         if datatype in ["jsonb"]:object_list[index][k]=json.dumps(v) if v else None
         if datatype in ["ARRAY"]:object_list[index][k]=v.split(",") if v else None
   background=BackgroundTasks()
   output=f"{len(object_list)} object updated"
   if mode=="background":
      if len(object_list)==1:background.add_task(await postgres_client.fetch_all(query=query,values=object_list[0]))
      else:background.add_task(await postgres_client.execute_many(query=query,values=object_list))
   else:
      if len(object_list)==1:output=await postgres_client.fetch_all(query=query,values=object_list[0])
      else:output=await postgres_client.execute_many(query=query,values=object_list)
   return {"status":1,"message":output}


