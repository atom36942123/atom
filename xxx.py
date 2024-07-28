@app.post("/{x}/parent")
async def function_parent(request:Request):
   
   # #add like count
   # if output:
   #    ids=list(set([item["id"] for item in output if item["id"]]))
   #    object_like_list=await request.state.postgres_object.fetch_all(query=f"select parent_id,count(*) from likes join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;",values={})
   #    for object in output:
   #       object["like_count"]=0
   #       for object_like in object_like_list:
   #          if object["id"]==object_like["parent_id"]:object["like_count"]=object_like["count"]
   # #add comment count
   # if output:
   #    ids=list(set([item["id"] for item in output if item["id"]]))
   #    object_comment_list=await request.state.postgres_object.fetch_all(query=f"select parent_id,count(*) from comment join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table='{table}' group by parent_id;",values={})
   #    for object in output:
   #       object["comment_count"]=0
   #       for object_comment in object_comment_list:
   #          if object["id"]==object_comment["parent_id"]:object["comment_count"]=object_comment["count"]
   #response
   

@router.get("/{x}/my-action-check")
async def function_my_action_check(request:Request,action:str,table:str,ids:str):
   #token check
   user=json.loads(jwt.decode(request.headers.get("token"),env("key"),algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x issue"}))
   #logic
   ids=[int(x) for x in ids.split(',')]
   output=await request.state.postgres_object.fetch_all(query=f"select parent_id from {action} join unnest(array{ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where parent_table=:parent_table and created_by_id=:created_by_id;",values={"parent_table":table,"created_by_id":user["id"]})
   ids_filtered=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #response
   return {"status":1,"message":ids_filtered}

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
