#env read
from environs import Env
env=Env()
env.read_env()

#env unpack
config_postgres_database_uri=env("config_postgres_database_uri")
config_mongo_server_uri=env("config_mongo_server_uri")
config_redis_server_uri=env("config_redis_server_uri")
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



