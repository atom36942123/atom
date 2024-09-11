#env
from environs import Env
env=Env()
env.read_env()
config_postgres_database_url=env("postgres_database_url")
config_redis_server_url=env("redis_server_url")
config_mongo_server_url=env("mongo_server_url")
config_sentry_dsn=env("sentry_dsn")
config_key_root=env("key_root")
config_key_jwt=env("key_jwt")
config_aws_default_region=env("aws_default_region")
config_aws_access_key_id=env("aws_access_key_id")
config_aws_secret_access_key=env("aws_secret_access_key")
config_s3_bucket_name=env("s3_bucket_name")
config_ses_sender_email=env("ses_sender_email")
config_elasticsearch_username=env("elasticsearch_username")
config_elasticsearch_password=env("elasticsearch_password")
config_elasticsearch_cloud_id=env("elasticsearch_cloud_id")
config_is_delete_account=env("is_delete_account")
config_is_delete_object_self=env("is_delete_object_self")

#postgres object
from databases import Database
config_postgres_object=Database(config_postgres_database_url,min_size=1,max_size=100)

#custom
config_column_datatype=None
