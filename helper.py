#env
from environs import Env
env=Env()
env.read_env()

#import
from fastapi import Request,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#function
error=lambda x:JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":x}))
query_runner=lambda x,y:await request.state.postgres_object.fetch_all(query=x,values=y)

#database
config_database={
"created_at":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"timestamptz","now()",None,1],"created_by_id":[["atom","users","post","likes","comment","bookmark","report","rating","block","message","helpdesk","file","otp","workseeker"],"bigint",None,None,1],"received_by_id":[["message"],"bigint",None,None,1],
"updated_at":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"timestamptz",None,None,0],"updated_by_id":[["atom","users","post","comment","report","message","helpdesk","workseeker"],"bigint",None,None,0],"is_pinned":[["post"],"int",0,(0,1),1],
"is_active":[["atom","users","post","comment","workseeker"],"int",1,(0,1),1],"is_verified":[["atom","users","post","comment","workseeker"],"int",0,(0,1),1],
"parent_table":[["likes","comment","bookmark","report","rating","block"],"text",None,None,1],"parent_id":[["likes","comment","bookmark","report","rating","block"],"bigint",None,None,1],
"firebase_id":[["users"],"text",None,None,1],"google_id":[["users"],"text",None,None,1],
"last_active_at":[["users"],"timestamptz","now()",None,0],"otp":[["otp"],"int",None,None,1],"last_active_at":[["users"],"timestamptz","now()",None,0],
"username":[["users"],"text",None,None,1],"password":[["users"],"text",None,None,1],
"profile_pic_url":[["users"],"text",None,None,0],"date_of_birth":[["users"],"date",None,None,0],"name":[["users","workseeker"],"text",None,None,0],"gender":[["users","workseeker"],"text",None,None,0],
"email":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],"mobile":[["users","post","otp","helpdesk","workseeker"],"text",None,None,1],"whatsapp":[["users","post","workseeker"],"text",None,None,1],"phone":[["users","post","workseeker"],"text",None,None,1],
"country":[["users","post",],"text",None,None,1],"state":[["users","post"],"text",None,None,1],"city":[["users","post"],"text",None,None,1],
"type":[["post","atom","users","helpdesk"],"text",None,None,1],"title":[["post","atom","users"],"text",None,None,0],"description":[["post","atom","users","comment","report","rating","block","message","helpdesk","workseeker"],"text",None,None,0],"file_url":[["post","atom","file"],"text",None,None,0],"link_url":[["post","atom"],"text",None,None,0],"tag":[["post","atom","users","workseeker"],"text[]",None,None,1],
"number":[["post"],"numeric",None,None,0],"date":[["post"],"date",None,None,0],"status":[["post","report","message","helpdesk"],"text",None,None,1],"remark":[["post","report","helpdesk"],"text",None,None,0],"rating":[["post","rating","helpdesk"],"int",None,None,0],
"work_type":[["workseeker"],"text",None,None,1],"work_profile":[["workseeker"],"text",None,None,1],
"degree":[["workseeker"],"text",None,None,0],"college":[["workseeker"],"text",None,None,0],"linkedin_url":[["workseeker"],"text",None,None,0],"portfolio_url":[["workseeker"],"text",None,None,0],"experience":[["workseeker"],"int",None,None,1],"experience_work_profile":[["workseeker"],"int",None,None,0],"is_working":[["workseeker"],"int",None,(0,1),1],
"location_current":[["workseeker"],"text",None,None,1],"location_expected":[["workseeker"],"text",None,None,1],
"currency":[["workseeker"],"text",None,None,0],"salary_frequency":[["workseeker"],"text",None,None,0],"salary_current":[["workseeker"],"int",None,None,0],"salary_expected":[["workseeker"],"int",None,None,0],
"sector":[["workseeker"],"text",None,None,0],"past_company_count":[["workseeker"],"int",None,None,0],"past_company_name":[["workseeker"],"text",None,None,0],
"marital_status":[["workseeker"],"text",None,None,0],"physical_disability":[["workseeker"],"text",None,None,0],"hobby":[["workseeker"],"text",None,None,0],"language":[["workseeker"],"text",None,None,0],
"joining_days":[["workseeker"],"int",None,None,1],"career_break_month":[["workseeker"],"int",None,None,0],"resume_url":[["workseeker"],"text",None,None,0],"achievement":[["workseeker"],"text",None,None,0],"certificate":[["workseeker"],"text",None,None,0],"project":[["workseeker"],"text",None,None,0],"is_founder":[["workseeker"],"int",None,(0,1),1],"soft_skill":[["workseeker"],"text",None,None,0],"tool":[["workseeker"],"text",None,None,0],"achievement_work":[["workseeker"],"text",None,None,0],
}

alter_query=[
"alter table users add constraint constraint_unique_username_users unique (username);",
"alter table likes add constraint constraint_unique_created_by_id_parent_table_parent_id_likes unique (created_by_id,parent_table,parent_id);",
"alter table bookmark add constraint constraint_unique_created_by_id_parent_table_parent_id_bookmark unique (created_by_id,parent_table,parent_id);",
"alter table report add constraint constraint_unique_created_by_id_parent_table_parent_id_report unique (created_by_id,parent_table,parent_id);",
"alter table block add constraint constraint_unique_created_by_id_parent_table_parent_id_block unique (created_by_id,parent_table,parent_id);",
"insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;",
"create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;"
]


