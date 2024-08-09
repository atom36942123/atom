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

config_database={
"created_at":["timestamptz","users,post,action,activity,box,atom"],
"created_by_id":["bigint","users,post,action,activity,box,atom"],
"updated_at":["timestamptz","users,post,action,activity,box,atom"],
"updated_by_id":["bigint","users,post,action,activity,box,atom"],
"is_active":["int","users,post,action,activity,box,atom"],
"is_verified":["int","users,post,action,activity,box,atom"],
"is_protected":["int","users,post,action,activity,box,atom"],
"type":["text","users,post,action,activity,box,atom"],
"status":["text","users,post,action,activity,box,atom"],
"remark":["text","users,post,action,activity,box,atom"],
"metadata":["jsonb","users,post,action,activity,box,atom"],
"parent_table":["text","action,activity"],
"parent_id":["bigint","action,activity"],
"last_active_at":["timestamptz","users"],
"google_id":["text","users"],
"otp":["int","box"],
"username":["text","users"],
"password":["text","users"],
"name":["text","users"],
"email":["text","users,post,box,atom"],
"mobile":["text","users,post,box,atom"],
"title":["text","users,post,box,atom"],
"description":["text","users,post,action,activity,box,atom"],
"tag":["text","users,post,box,atom"],
"link":["text","users,post,box,atom"],
"file":["text","users,post,box,atom"],
"rating":["numeric","users,post,box,atom"],
}
