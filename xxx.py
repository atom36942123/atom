
#schema
class schema_atom(BaseModel):
    id:int|None=None
    created_at:datetime|None=None
    created_by_id:int|None=None
    updated_at:datetime|None=None
    updated_by_id:int|None=None
    is_active:int|None=None
    is_verified:int|None=None
    parent_table:str|None=None
    parent_id:int|None=None
    received_by_id:int|None=None
    last_active_at:datetime|None=None
    firebase_id:str|None=None
    google_id:str|None=None
    otp:int|None=None
    metadata:dict|None=None
    username:str|None=None
    password:str|None=None
    profile_pic_url:str|None=None
    date_of_birth:datetime|None=None
    name:str|None=None
    gender:str|None=None
    email:str|None=None
    mobile:str|None=None
    whatsapp:str|None=None
    phone:str|None=None
    country:str|None=None
    state:str|None=None
    city:str|None=None
    type:str|None=None
    title:str|None=None
    description:str|None=None
    file_url:str|None=None
    link_url:str|None=None
    tag:list|None=None
    date:datetime|None=None
    status:str|None=None
    remark:str|None=None
    rating:float|None=None
    is_pinned:int|None=None
    work_type:str|None=None
    work_profile:str|None=None
    degree:str|None=None
    college:str|None=None
    linkedin_url:str|None=None
    portfolio_url:str|None=None
    experience:int|None=None
    experience_work_profile:int|None=None
    is_working:int|None=None
    location_current:str|None=None
    location_expected:str|None=None
    currency:str|None=None
    salary_frequency:str|None=None
    salary_current:int|None=None
    salary_expected:int|None=None
    sector:str|None=None
    past_company_count:int|None=None
    past_company_name:str|None=None
    marital_status:str|None=None
    physical_disability:str|None=None
    hobby:str|None=None
    language:str|None=None
    joining_days:int|None=None
    career_break_month:int|None=None
    resume_url:str|None=None
    achievement:str|None=None
    certificate:str|None=None
    project:str|None=None
    is_founder:int|None=None
    soft_skill:str|None=None
    tool:str|None=None
    achievement_work:str|None=None







    


@router.get("/{x}/my-action-check")
async def function_my_action_check(request:Request,action:str,table:str,ids:str):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #ids into list
    if not ids:return function_http_response(400,0,f"ids cant be null")
    try:ids=[int(x) for x in ids.split(',')]
    except Exception as e:return function_http_response(400,0,e.args)
    #logic
    query=f"select parent_id from {action} join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;"
    values={"parent_table":table,"created_by_id":request_user["id"]}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #parent ids join
    try:ids_filtered=list(set([item["parent_id"] for item in response["message"] if item["parent_id"]]))
    except Exception as e:return function_http_response(400,0,e.args)
    #final response
    return {"status":1,"message":ids_filtered}

@router.get("/{x}/my-read-parent/{table}/{parent_table}/{page}")
async def function_my_read_parent(request:Request,table:str,parent_table:str,page:int):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #read parent ids
    limit=30
    offset=(page-1)*limit
    query=f"select parent_id from {table} where created_by_id=:created_by_id and parent_table=:parent_table order by id desc offset {offset} limit {limit};"
    values={"created_by_id":request_user["id"],"parent_table":parent_table}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    parent_ids=[x["parent_id"] for x in response["message"]]
    #read parent ids objects
    query=f"select * from {parent_table} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
    response=await function_query_runner(request.state.postgres_object,"read",query,{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add like count
    response=await function_add_like_count(request.state.postgres_object,function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add comment count
    response=await function_add_comment_count(request.state.postgres_object,function_query_runner,parent_table,response["message"])
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return response


@router.get("/{x}/my-message-thread/{user_id}/{page}")
async def function_my_message_thread(request:Request,user_id:int,page:int,background_tasks:BackgroundTasks):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    limit=30
    offset=(page-1)*limit
    query=f"select * from message where (created_by_id=:user_1 and received_by_id=:user_2) or (created_by_id=:user_2 and received_by_id=:user_1) order by id desc offset {offset} limit {limit}"
    values={"user_1":request_user["id"],"user_2":user_id}
    response=await function_query_runner(request.state.postgres_object,"read",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #add user key
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"received_by_id")
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #background task
    query=f"update message set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where received_by_id=:received_by_id and created_by_id=:created_by_id returning *;"
    values={"status":"read","updated_by_id":request_user['id'],"updated_at":datetime.now(),"received_by_id":request_user['id'],"created_by_id":user_id}
    background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",query,values)
    #final response
    return response

@router.delete("/{x}/my-delete")
async def function_my_delete(request:Request,x:str,background_tasks:BackgroundTasks,mode:Literal["post_all","comment_all","message_all","like_post_all","bookmark_post_all","message","message_thread","like_post","bookmark_post","account"],user_id:int=None,post_id:int=None,message_id:int=None):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #refresh request_user
    response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return function_http_response(400,0,"no user for token passed")
    request_user=response["message"][0]
    #query set
    if mode=="comment_all":query,values="delete from comment where created_by_id=:created_by_id;",{"created_by_id":request_user['id']}
    if mode=="message_all":query,values="delete from message where created_by_id=:created_by_id or received_by_id=:received_by_id;",{"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="like_post_all":query,values="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table;",{"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="bookmark_post_all":query,values="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table;",{"created_by_id":request_user['id'],"parent_table":"post"}
    if mode=="message_thread":query,values="delete from message where (created_by_id=:a and received_by_id=:b) or (created_by_id=:b and received_by_id=:a);",{"a":request_user['id'],"b":user_id}   
    if mode=="like_post":query,values="delete from likes where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;",{"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    if mode=="bookmark_post":query,values="delete from bookmark where created_by_id=:created_by_id and parent_table=:parent_table and parent_id=:parent_id;",{"created_by_id":request_user['id'],"parent_table":"post","parent_id":post_id}
    if mode=="message":query,values=f"delete from message where id=:id and (created_by_id=:created_by_id or received_by_id=:received_by_id);",{"id":message_id,"created_by_id":request_user['id'],"received_by_id":request_user['id']}
    if mode=="post_all":
        if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"user type not allowed")
        query,values="delete from post where created_by_id=:created_by_id;",{"created_by_id":request_user['id']}
    if mode=="account":
        if request_user["type"] in ["root","admin"]:return function_http_response(400,0,"not allowed")
        query,values="delete from users where id=:id;",{"id":request_user['id']}
        for item in ["post","likes","bookmark","report","rating","comment","block"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where created_by_id=:created_by_id;",{"created_by_id":request_user['id']})
        for item in ["message"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where created_by_id=:created_by_id or received_by_id=:received_by_id;",{"created_by_id":request_user['id'],"received_by_id":request_user['id']})
        for item in ["likes","bookmark","comment","rating","block","report"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where parent_table='users' and parent_id=:parent_id;",{"parent_id":request_user['id']})
    #query run
    response=await function_query_runner(request.state.postgres_object,"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return {"status":1,"message":"object deleted"}

@router.post("/{x}/object-create/{table}")
async def function_object_create(table:str,request:Request,body:schema_atom):
   #token check
   if table not in ["helpdesk","workseeker"] or request.headers.get("token"):
      response=await function_token_decode(request,env("key"))
      if response["status"]==0:return function_http_response(400,0,response["message"])
      request_user=response["message"]
   else:request_user,request_user["id"]={},None
   #param
   param={k: v for k, v in vars(body).items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"body cant be null")
   if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
   if "number" in param:param["number"]=round(param["number"],5)
   param["created_by_id"]=request_user["id"]
   if table=="message":param["status"]="unread"
   #logic
   query=f'''insert into {table} ({",".join([*param])}) values ({",".join([":"+item for item in [*param]])}) returning *;'''
   response=await function_query_runner(request.state.postgres_object,"write",query,param)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.put("/{x}/object-update/{table}/{id}")
async def function_object_update(request:Request,table:str,id:int,body:schema_atom):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #refresh request_user
   response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   request_user=response["message"][0]
   #param
   param={k: v for k, v in vars(body).items() if v not in [None,""," "]}
   if not param:return function_http_response(400,0,"body cant be null")
   if "metadata" in param:param["metadata"]=json.dumps(param["metadata"],default=str)
   if "number" in param:param["number"]=round(param["number"],5)
   param["updated_at"],param["updated_by_id"]=datetime.now(),request_user["id"]
   #non admin case
   id,created_by_id=id,None
   if request_user["type"] not in ["root","admin"]:
      if table=="users":id,created_by_id=request_user['id'],None
      else:id,created_by_id=id,request_user['id']
      for item in ["created_at","created_by_id","received_by_id","is_active","is_verified","type"]:param.pop(item,None)
   #logic
   key=""
   for k,v in param.items():key=key+f"{k}=coalesce(:{k},{k}) ,"
   query=f"update {table} set {key.strip().rsplit(',', 1)[0]} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   response=await function_query_runner(request.state.postgres_object,"write",query,param|{"id":id,"created_by_id":created_by_id})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.delete("/{x}/object-delete/{table}/{id}")
async def function_object_delete(request:Request,table:str,id:int,background_tasks:BackgroundTasks):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #refresh request_user
   response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no user for token passed")
   request_user=response["message"][0]
   #table check
   if table in ["users"]:return function_http_response(400,0,"table not allowed")
   #read object
   response=await function_query_runner(request.state.postgres_object,"read",f"select * from {table} where id={id};",{})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   if not response["message"]:return function_http_response(400,0,"no such object")
   object=response["message"][0]
   #permission check
   id,created_by_id=id,None
   if request_user["type"] not in ["root"]:
      if table=="users":id,created_by_id=request_user['id'],None
      else:id,created_by_id=id,request_user['id']
   #logic
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   response=await function_query_runner(request.state.postgres_object,"write",query,{"id":id,"created_by_id":created_by_id})
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #background task
   for item in ["likes","bookmark","comment","rating","block","report"]:background_tasks.add_task(function_query_runner,request.state.postgres_object,"write",f"delete from {item} where parent_table=:parent_table and parent_id=:parent_id;",{"parent_table":table,"parent_id":id})
   if "file_url" in object:background_tasks.add_task(function_s3_delete_url,env.list("aws")[0],env.list("aws")[1],env.list("s3")[0],object["file_url"])
   #final response
   return {"status":1,"message":"object deleted"}

@router.get("/{x}/object-read-self/{table}/{page}")
async def function_object_read_self(request:Request,table:str,page:int,id:int=None,mode:str=None,limit:int=30):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #table=users
   if table=="users":
      response=await function_query_runner(request.state.postgres_object,"read","select * from users where id=:id;",{"id":request_user["id"]})
      if response["status"]==0:return function_http_response(400,0,response["message"])
      if not response["message"]:return function_http_response(400,0,"no user for token passed")
      return {"status":1,"message":response["message"][0]}
   #table!=users
   query,values=f"select * from {table} where (created_by_id=:created_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"created_by_id":request_user['id'],"id":id}
   if mode=="receiver":query,values=f"select * from {table} where (received_by_id=:received_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"received_by_id":request_user['id'],"id":id}
   if mode=="all":query,values=f"select * from {table} where (created_by_id=:created_by_id or received_by_id=:received_by_id) and (id=:id or :id is null) order by id desc offset {(page-1)*limit} limit {limit};",{"created_by_id":request_user['id'],"received_by_id":request_user['id'],"id":id}
   response=await function_query_runner(request.state.postgres_object,"read",query,values)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add count key
   if table in ["post"]:
      response=await function_add_like_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      response=await function_add_comment_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/object-read-public/{table}/{page}")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_object_read_public(request:Request,table:Literal["users","atom","post","comment","workseeker"],page:int,limit:int=30):
   #logic
   response=await function_object_read(request.state.postgres_object,function_query_runner,table,dict(request.query_params),["id","desc"],limit,(page-1)*limit,schema_atom)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add user key
   response=await function_add_user_key(request.state.postgres_object,function_query_runner,response["message"],"created_by_id")
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #add count key
   if table in ["post"]:
      response=await function_add_like_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
      response=await function_add_comment_count(request.state.postgres_object,function_query_runner,table,response["message"])
      if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/object-read-admin/{table}/{page}")
async def function_object_read_admin(request:Request,table:str,page:int,limit:int=30):
   #token check
   response=await function_token_decode(request,env("key"))
   if response["status"]==0:return function_http_response(400,0,response["message"])
   request_user=response["message"]
   #permission check
   if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
   if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
   #logic
   response=await function_object_read(request.state.postgres_object,function_query_runner,table,dict(request.query_params),["id","desc"],limit,(page-1)*limit,schema_atom)
   if response["status"]==0:return function_http_response(400,0,response["message"])
   #final response
   return response

@router.get("/{x}/pcache")
@cache(expire=60)
async def function_pcache(request:Request):    
    #logic
    output={}
    output["mapping_post_type"]={"funding123":"startup idea"}
    output["switch"]={"listing":0}
    output["admin_type"]=["root","admin"]
    #post type tag
    output["post_tag_type"]={}
    response=await function_query_runner(request.state.postgres_object,"read","select distinct(type) from post where type is not null;",{})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    type_list=[item["type"] for item in response["message"] if item["type"]]
    for item in type_list:
        response=await function_query_runner(request.state.postgres_object,"read",f"with x as (select unnest(tag) as tag from post where type='{item}' and tag is not null) select tag,count(*) from x group by tag order by count desc limit 1000;",{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        output["post_tag_type"][item]=response["message"]
    #query
    query_dict={
    "post_tag":"with x as (select unnest(tag) as tag from post where tag is not null) select tag,count(*) from x group by tag order by count desc;",
    "user_tag":"with x as (select unnest(tag) as tag from users where tag is not null) select tag,count(*) from x group by tag order by count desc;",
    "user_count":"select count(*) from users;",
    "logo":"select * from atom where type='logo' and is_active=1 limit 1;",
    "about":"select * from atom where type='about' and is_active=1 limit 1;",
    "post_tag_trending":"select * from atom where type='post_tag_trending' and is_active=1 limit 1;",
    "curated":"select * from atom where type='curated' and is_active=1 order by id asc limit 1000;",
    "link":"select * from atom where type='link' and is_active=1 order by id asc limit 10;",
    }
    for k,v in query_dict.items():
        response=await function_query_runner(request.state.postgres_object,"read",v,{})
        if response["status"]==0:return function_http_response(400,0,response["message"])
        output[k]=response["message"]
    #final response
    return {"status":1,"message":output}



@router.put("/{x}/update-cell")
async def function_update_cell(request:Request,table:str,id:int,column:str,value:str):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #conversion
    response=await function_query_runner(request.state.postgres_object,"read","select data_type from information_schema.columns where column_name=:column_name limit 1;",{"column_name":column})
    if response["status"]==0:return function_http_response(400,0,response["message"])
    if not response["message"]:return {"status":0,"message":"no such column"}
    datatype=response["message"][0]["data_type"]
    if datatype in ["decimal","numeric","real","double precision"]:value=round(float(value),2)
    if datatype=="ARRAY":value=value.split(",")
    if datatype=="jsonb":value=json.dumps(value,default=str)
    if datatype=="integer":value=int(value)
    if datatype=="integer":value=int(value)
    if datatype=="timestamp with time zone":value=datetime.strptime(value,'%Y-%m-%d')
    if column in ["password","firebase_id","google_id"]:value=hashlib.sha256(value.encode()).hexdigest()
    #admin check
    id,created_by_id=id,None
    if request_user["type"] not in ["root","admin"]:
        if table=="users":id,created_by_id=request_user['id'],None
        else:id,created_by_id=id,request_user['id']
        if column in ["created_by_id","received_by_id","is_active","is_verified","type"]:return function_http_response(400,0,"column not allowed")
    #logic
    query=f"update {table} set {column}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
    values={"value":value,"updated_at":datetime.now(),"updated_by_id":request_user['id'],"id":id,"created_by_id":created_by_id}
    response=await function_query_runner(request.state.postgres_object,"write",query,values)
    if response["status"]==0:return function_http_response(400,0,response["message"])
    #final response
    return response


@router.get("/{x}/aws")
async def function_aws(request:Request,background_tasks:BackgroundTasks,mode:str,filename:str=None):
    #token check
    response=await function_token_decode(request,env("key"))
    if response["status"]==0:return function_http_response(400,0,response["message"])
    request_user=response["message"]
    #logic
    if mode=="create-s3-url":
        boto_client=boto3.client("s3",aws_access_key_id=env.list("aws")[0],aws_secret_access_key=env.list("aws")[1],region_name=env.list("s3")[1])
        output=boto_client.generate_presigned_post(Bucket=env.list("s3")[0],Key=str(uuid.uuid4())+"-"+filename,ExpiresIn=1000,Conditions=[['content-length-range',1,1024*1000]])
        background_tasks.add_task(function_query_runner,request.state.postgres_object,"write","insert into file (created_by_id,file_url) values (:created_by_id,:file_url) returning *;",{"created_by_id":request_user["id"],"file_url":output['url']+output['fields']['key']})
        return {"status":1,"message":output}
    #final response
    return None



@router.get("/{x}/{function}")
async def function_function(request:Request,function:str,background_tasks:BackgroundTasks,filename:str=None,url:str=None,email:str=None,title:str=None,description:str=None,mode:str=None,query:str=None):
    #logic
    if function=="delete-s3-url":
        if not url:return function_http_response(400,0,"url must")
        if request_user["is_active"]!=1:return function_http_response(400,0,"only active user allowed")
        if request_user["type"] not in ["root","admin"]:return function_http_response(400,0,"only admin allowed")
        response=await function_s3_delete_url(env.list("aws")[0],env.list("aws")[1],env.list("s3")[0],url)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="send-email-ses":
        if any(not item for item in [email,title,description]):return function_http_response(400,0,"email/title/description must")
        response=await function_ses_send_email(env.list("aws")[0],env.list("aws")[1],env.list("ses")[0],env.list("ses")[1],email,title,description)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="send-otp-email":
        if not email:return function_http_response(400,0,"email must")
        otp=random.randint(100000,999999)
        response=await function_ses_send_email(env.list("aws")[0],env.list("aws")[1],env.list("ses")[0],env.list("ses")[1],email,"otp from atom",str(otp))
        if response["status"]==0:return function_http_response(400,0,response["message"])
        response=await function_query_runner(request.state.postgres_object,"write","insert into otp (created_by_id,otp,email) values (:created_by_id,:otp,:email) returning *;",{"created_by_id":None,"otp":otp,"email":email})
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="database-clean":
        response=await function_database_clean(request.state.postgres_object,function_query_runner)
        if response["status"]==0:return function_http_response(400,0,response["message"])
    if function=="mongo":
        body=await request.json()
        if not mode:return function_http_response(400,0,"mode must")
        mongo_object=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
        if mode=="create":response=await mongo_object.test.users.insert_one(body)
        if mode=="read":response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
        if mode=="update":response=await mongo_object.test.users.update_one({"_id":ObjectId(body["id"])},{"$set":body})
        if mode=="delete":response=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
    if function=="elasticsearch":
        body=await request.json()
        if not mode:return function_http_response(400,0,"mode must")
        elasticsearch_object=Elasticsearch(cloud_id=cloud_id,basic_auth=(username,password))
        if mode=="create":response=elasticsearch_object.index(index="users",id=body["id"],document=body)
        if mode=="read":response=elasticsearch_object.get(index="users",id=body["id"])
        if mode=="update":response=elasticsearch_object.update(index="users",id=body["id"],doc=body)
        if mode=="delete":response=elasticsearch_object.delete(index="users",id=body["id"])
        if mode=="refresh":response=elasticsearch_object.indices.refresh(index="users")
        if mode=="search":response=elasticsearch_object.search(index="users",body={"query":{"match":{column:keyword}},"size":30})
    #final response
    return response



#function
from fastapi import Request,Response
def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):
    return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])

async def function_object_read(postgres_object,function_query_runner,table,param,order,limit,offset,schema_atom):
   #param
   param={k:v for k,v in param.items() if v not in [None,""," "]}
   if "tag" in param and param["tag"]:param["tag"]=param["tag"].split(",")
   param_schema_atom={k:v for k,v in vars(schema_atom(**param)).items() if v not in [None,""," "]}
   #operator
   operator={}
   for k,v in param_schema_atom.items():
       operator_name=f"{k}_operator"
       if operator_name in param:operator[k]=param[operator_name]
   #where
   where="where "
   for k,v in param_schema_atom.items():
      if k in operator:where=where+f"({k} {operator[k]} :{k} or :{k} is null) and "
      elif k=="tag":where=where+f"({k} @> :{k} or :{k} is null) and "
      else:where=where+f"({k} = :{k} or :{k} is null) and "
   where=where.strip().rsplit('and',1)[0]
   if where=="where":where=""
   #logic
   query=f"select * from {table} {where} order by {order[0]} {order[1]} limit {limit} offset {offset};"
   response=await function_query_runner(postgres_object,"read",query,param_schema_atom)
   if response["status"]==0:return response
   #final response
   return response



async def function_add_like_count(postgres_object,function_query_runner,table,object_list):
   #check
   if not object_list:return {"status":1,"message":object_list}
   #fetch count
   ids=list(set([item["id"] for item in object_list if item["id"]]))
   query=f"select parent_id,count(*) from likes join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;"
   response=await function_query_runner(postgres_object,"read",query,{})
   if response["status"]==0:return response
   object_like_list=response["message"]
   #set count
   for object in object_list:
      object["like_count"]=0
      for object_like in object_like_list:
         if object["id"]==object_like["parent_id"]:object["like_count"]=object_like["count"]
   #final response
   return {"status":1,"message":object_list}

async def function_add_comment_count(postgres_object,function_query_runner,table,object_list):
   #check
   if not object_list:return {"status":1,"message":object_list}
   #fetch count
   ids=list(set([item["id"] for item in object_list if item["id"]]))
   query=f"select parent_id,count(*) from comment join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;"
   response=await function_query_runner(postgres_object,"read",query,{})
   if response["status"]==0:return response
   object_comment_list=response["message"]
   #set count
   for object in object_list:
      object["comment_count"]=0
      for object_comment in object_comment_list:
         if object["id"]==object_comment["parent_id"]:object["comment_count"]=object_comment["count"]
   #final response
   return {"status":1,"message":object_list}





import boto3
async def function_s3_delete_url(access_key_id,secret_access_key,bucket_name,url):
   if not url:return {"status":1,"message":"url null"}
   key_list=[item.split("/")[-1] for item in url.split(",") if bucket_name in item]
   try:output=list(map(lambda x:boto3.resource("s3",aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key).Object(bucket_name,x).delete(),key_list))
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":output}

import boto3
async def function_ses_send_email(access_key_id,secret_access_key,ses_sender,ses_region,to,title,description):
   try:output=boto3.client("ses",region_name=ses_region,aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key).send_email(Source=ses_sender,Destination={"ToAddresses":[to]},Message={"Subject":{"Charset":"UTF-8","Data":title},"Body":{"Text":{"Charset":"UTF-8","Data":description}}})
   except Exception as e:return {"status":0,"message":e.args}
   return {"status":1,"message":output}

async def function_update_mat_all(postgres_object,function_query_runner):
   #logic
   read_mat_all="select string_agg(oid::regclass::text,', ') as output from pg_class where relkind='m';"
   response=await function_query_runner(postgres_object,"read",read_mat_all,{})
   if response["status"]==0:return response
   mat_all_list=response["message"][0]["output"].split(",")
   for item in mat_all_list:
      query=f"refresh materialized view {item};"
      response=await function_query_runner(postgres_object,"write",query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_mat(postgres_object,function_query_runner):
   #logic
   drop_all_mat_get_query="select 'drop materialized view ' || string_agg(oid::regclass::text, ', ') || ' cascade;' as output from pg_class where relkind='m';"
   response=await function_query_runner(postgres_object,"read",drop_all_mat_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_index(postgres_object,function_query_runner):
   #logic
   drop_all_index_get_query='''
   select 'drop index ' || string_agg(i.indexrelid::regclass::text, ', ' order by n.nspname, 
   i.indrelid::regclass::text, cl.relname) as output
   from pg_index i
   join pg_class cl ON cl.oid = i.indexrelid
   join   pg_namespace n ON n.oid = cl.relnamespace
   left join pg_constraint co ON co.conindid = i.indexrelid
   where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null
   and not i.indisprimary and not i.indisunique and not i.indisexclusion 
   and not i.indisclustered and not i.indisreplident;
   '''
   response=await function_query_runner(postgres_object,"read",drop_all_index_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   #final response
   return {"status":1,"message":"done"}

async def function_drop_all_view(postgres_object,function_query_runner):
   drop_all_view_get_query='''select 'drop view if exists ' || string_agg (table_name, ', ') || ' cascade;' as output from information_schema.views where table_schema not in ('pg_catalog', 'information_schema') and table_name !~ '^pg_';'''
   response=await function_query_runner(postgres_object,"read",drop_all_view_get_query,{})
   if response["status"]==0:return response
   drop_all_query=response["message"][0]["output"]
   if drop_all_query:
      response=await function_query_runner(postgres_object,"write",drop_all_query,{})
      if response["status"]==0:return response
   return {"status":1,"message":"done"}

async def function_database_clean(postgres_object,function_query_runner):
   #logic
   query_dict={
   "delete_post_creator_null":"delete from post where id in (select x.id from post as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_likes_creator_null":"delete from likes where id in (select x.id from likes as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_bookmark_creator_null":"delete from bookmark where id in (select x.id from bookmark as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_report_creator_null":"delete from report where id in (select x.id from report as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_comment_creator_null":"delete from comment where id in (select x.id from comment as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_rating_creator_null":"delete from rating where id in (select x.id from rating as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_block_creator_null":"delete from block where id in (select x.id from block as x left join users as y on x.created_by_id=y.id where x.created_by_id is not null and y.id is null);",
   "delete_likes_parent_null_post":"delete from likes where id in (select x.id from likes as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_bookmark_parent_null_post":"delete from bookmark where id in (select x.id from bookmark as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_comment_parent_null_post":"delete from comment where id in (select x.id from comment as x left join post as y on x.parent_id=y.id where x.parent_table='post' and y.id is null);",
   "delete_duplicate_tag":"delete from atom as a1 using atom as a2 where a1.type='tag' and a2.type='tag' and a1.ctid>a2.ctid and a1.title=a2.title;",
   "delete_message_old":"delete from message where created_at<now()-interval '30 days';",
   }
   for k,v in query_dict.items():
      response=await function_query_runner(postgres_object,"write",v,{})
      if response["status"]==0:return response
   return {"status":1,"message":"done"}
