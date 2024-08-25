#env
from environs import Env
env=Env()
env.read_env()
config_postgres_database_url=env("config_postgres_database_url")
config_redis_server=env("config_redis_server")
config_mongo_server=env("config_mongo_server")
config_sentry_dsn=env("config_sentry_dsn")
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

#postgres object
from databases import Database
postgres_object=Database(config_postgres_database_url,min_size=1,max_size=100)

#elasticsearch object
from elasticsearch import Elasticsearch
elasticsearch_object=Elasticsearch(cloud_id=config_elasticsearch_cloud_id,basic_auth=(config_elasticsearch_username,config_elasticsearch_password))

#mongo object
import motor.motor_asyncio
mongo_object=motor.motor_asyncio.AsyncIOMotorClient(config_mongo_server)

#database
config_database_extension=["create extension if not exists postgis;"]
config_database_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp"]
config_database_column={
"id":["bigint",config_database_table],
"created_at":["timestamptz",config_database_table],
"created_by_id":["bigint",config_database_table],
"updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
"updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
"is_active":["int",["users","post"]],
"is_verified":["int",["users","post"]],
"is_protected":["int",["users","post","box","atom"]],
"parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
"parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
"type":["text",["users","post","box","atom","helpdesk"]],
"status":["text",["report","helpdesk","message"]],
"remark":["text",["report","helpdesk"]],
"rating":["numeric",["rating","atom"]],
"metadata":["jsonb",["users","post","box","atom"]],
"username":["text",["users"]],
"password":["text",["users"]],
"google_id":["text",["users"]],
"profile_pic_url":["text",["users"]],
"last_active_at":["timestamptz",["users"]],
"name":["text",["users"]],
"email":["text",["users","post","box","atom","otp","helpdesk"]],
"mobile":["text",["users","post","box","atom","otp","helpdesk"]],
"date_of_birth":["date",["users"]],
"title":["text",["users","post","box","atom"]],
"description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
"file_url":["text",["post","box","atom","comment","message"]],
"link_url":["text",["post","box","atom"]],
"tag":["text",["users","post","box","atom"]],
"otp":["int",["otp"]],
"tag_array":["text[]",["atom"]],
"location":["geography(POINT)",["users","post","box","atom"]],
}
config_database_column_not_null={
"parent_table":["likes","bookmark","report","block","rating","comment","message"],
"parent_id":["likes","bookmark","report","block","rating","comment","message"]
}
config_database_index={
"type":"btree",
"is_verified":"btree",
"is_active":"btree",
"created_by_id":"btree",
"status":"btree",
"parent_table":"btree",
"parent_id":"btree",
"email":"btree",
"password":"btree",
"created_at":"brin",
"location":"gist"
}
config_database_query_misc=[
"alter table users add constraint constraint_unique_users unique (username);",
"alter table likes add constraint constraint_unique_likes unique (created_by_id,parent_table,parent_id);",
"alter table bookmark add constraint constraint_unique_bookmark unique (created_by_id,parent_table,parent_id);",
"alter table report add constraint constraint_unique_report unique (created_by_id,parent_table,parent_id);",
"alter table block add constraint constraint_unique_block unique (created_by_id,parent_table,parent_id);",
"insert into users (username,password,type,is_protected) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','admin',1) on conflict do nothing;",
"create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;",
]
