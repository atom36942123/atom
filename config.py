#env read
from environs import Env
env=Env()
env.read_env()

#env unpack
config_postgres_database_uri=env("config_postgres_database_uri")
config_redis_server_uri=env("config_redis_server_uri")
config_mongo_server_uri=env("config_mongo_server_uri")
config_key_root=env("config_key_root")
config_key_jwt=env("config_key_jwt")
config_aws_access_key_id=env("config_aws_access_key_id")
config_aws_secret_access_key=env("config_aws_secret_access_key")
config_s3_bucket_name=env("config_s3_bucket_name")
config_s3_region_name=env("config_s3_region_name")
config_ses_sender_email=env("config_ses_sender_email")
config_ses_region_name=env("config_ses_region_name")
config_elasticsearch_username=env("config_elasticsearch_username")
config_elasticsearch_password=env("config_elasticsearch_password")
config_elasticsearch_cloud_id=env("config_elasticsearch_cloud_id")

#database
config_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp"]
config_index_datatype_mapping={"text":"btree","bigint":"btree","integer":"btree","numeric":"btree","timestamp with time zone":"brin","date":"brin","jsonb":"gin","ARRAY":"gin"}
config_index=["type","is_verified","is_active","created_by_id","status","parent_table","parent_id","email","password","created_at"]
config_column={
"created_at":["timestamptz",config_table],
"created_by_id":["bigint",config_table],
"updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
"updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
"is_active":["int",["users","post"]],
"is_verified":["int",["users","post"]],
"is_protected":["int",["users","post","box","atom"]],
"type":["text",["users","post","box","atom","helpdesk"]],
"status":["text",["report","helpdesk","message"]],
"remark":["text",["report","helpdesk"]],
"metadata":["jsonb",["users","post","box","atom"]],
"parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
"parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
"last_active_at":["timestamptz",["users"]],
"google_id":["text",["users"]],
"otp":["int",["otp"]],
"username":["text",["users"]],
"password":["text",["users"]],
"name":["text",["users"]],
"email":["text",["users","post","box","atom","otp"]],
"mobile":["text",["users","post","box","atom","otp"]],
"title":["text",["users","post","box","atom"]],
"description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
"tag":["text",["users","post","box","atom"]],
"link":["text",["post","box","atom"]],
"file":["text",["post","box","atom"]],
"rating":["numeric",["rating"]],
}
config_column_not_null={
"parent_table":["likes","bookmark","report","block","rating","comment","message"],
"parent_id":["likes","bookmark","report","block","rating","comment","message"]
}
config_query_zzz=[
"alter table users add constraint constraint_unique_users unique (username);",
"alter table likes add constraint constraint_unique_likes unique (created_by_id,parent_table,parent_id);",
"alter table bookmark add constraint constraint_unique_bookmark unique (created_by_id,parent_table,parent_id);",
"alter table report add constraint constraint_unique_report unique (created_by_id,parent_table,parent_id);",
"alter table block add constraint constraint_unique_block unique (created_by_id,parent_table,parent_id);",
]




