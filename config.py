#env read
import os
from dotenv import load_dotenv
load_dotenv()

#env variables
redis_server_url=os.getenv("redis_server_url")
postgres_database_url=os.getenv("postgres_database_url")
secret_key_jwt=os.getenv("secret_key_jwt")
secret_key_root=os.getenv("secret_key_root")
sentry_dsn=os.getenv("sentry_dsn")
secret_key_openai=os.getenv("secret_key_openai")
aws_access_key_id=os.getenv("aws_access_key_id")
aws_secret_access_key=os.getenv("aws_secret_access_key")

#postgres schema default
postgres_schema_default={
"extension":["postgis"],
"table":["atom","human","users","post","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"],
"column":{
"created_at":["timestamptz",["atom","human","users","post","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"]],
"created_by_id":["bigint",["atom","human","users","post","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"]],
"updated_at":["timestamptz",["atom","human","users","post","report","comment","message","helpdesk"]],
"updated_by_id":["bigint",["atom","human","users","post","report","comment","message","helpdesk"]],
"is_active":["int",["users","post","comment"]],
"is_verified":["int",["users","post","comment"]],
"is_protected":["int",["users","post"]],
"is_deleted":["int",[]],
"parent_table":["text",["likes","bookmark","report","block","rating","comment"]],
"parent_id":["bigint",["likes","bookmark","report","block","rating","comment"]],
"user_id":["bigint",["message"]],
"location":["geography(POINT)",["users","post"]],
"api":["text",["log"]],
"status_code":["int",["log"]],
"response_time_ms":["numeric",["log"]],
"type":["text",["atom","human","users","post","helpdesk"]],
"status":["text",["report","helpdesk","message"]],
"remark":["text",["report","helpdesk"]],
"rating":["numeric",["rating"]],
"metadata":["jsonb",["users","post"]],
"username":["text",["users"]],
"password":["text",["users"]],
"google_id":["text",["users"]],
"profile_pic_url":["text",["users"]],
"last_active_at":["timestamptz",["users"]],
"name":["text",["users","human"]],
"email":["text",["users","post","otp","helpdesk","human"]],
"mobile":["text",["users","post","otp","helpdesk","human"]],
"date_of_birth":["date",["users"]],
"title":["text",["post","atom"]],
"description":["text",["users","post","atom","report","block","comment","message","helpdesk"]],
"file_url":["text",["post","atom","comment","message"]],
"link_url":["text",["post","atom"]],
"tag":["text",["users","post","atom"]],
"otp":["int",["otp"]],
"tag_array":["text[]",[]],
"interest":["text",["users"]],
"skill":["text",["users"]],
"gender":["text",["users"]],
"country":["text",["users","human"]],
"state":["text",["users","human"]],
"city":["text",["users","human"]],
"api_access":["text",["users"]]
},
"index":{
"created_at":["brin",["users","post"]],
"created_by_id":["btree",["post","likes","bookmark","report","block","rating","comment","message"]],
"is_active":["btree",["users","post","comment"]],
"is_verified":["btree",["users","post","comment"]],
"parent_table":["btree",["likes","bookmark","report","block","rating","comment"]],
"parent_id":["btree",["likes","bookmark","report","block","rating","comment"]],
"user_id":["btree",["message"]],
"type":["btree",["atom","human","users","post","helpdesk"]],
"status":["btree",["report","helpdesk"]],
"email":["btree",["users","post","otp","helpdesk","human"]],
"mobile":["btree",["users","post","otp","helpdesk","human"]],
"password":["btree",["users"]],
"location":["gist",["users","post"]],
"tag":["btree",["users","post","atom"]],
"tag_array":["gin",[]]
},
"not_null":{
"parent_table":["likes","bookmark","report","block","rating","comment"],
"parent_id":["likes","bookmark","report","block","rating","comment"],
"user_id":["message"],
"created_by_id":["message"]
},
"unique":{
"username":["users"],
"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"]
},
"bulk_delete_disable":{
"users":1
},
"query":{
"create_root_user":"insert into users (username,password) values ('atom','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3') on conflict do nothing;",
"delete_disable_root_user":"create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;"
}
}

