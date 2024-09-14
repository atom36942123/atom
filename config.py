#env
from environs import Env
env=Env()
env.read_env()
postgres_database_url=env("postgres_database_url")
redis_server_url=env("redis_server_url")
mongo_server_url=env("mongo_server_url")
sentry_dsn=env("sentry_dsn")
jwt_secret_key=env("jwt_secret_key")


aws_default_region=env("aws_default_region")
aws_access_key_id=env("aws_access_key_id")
aws_secret_access_key=env("aws_secret_access_key")
s3_bucket_name=env("s3_bucket_name")
ses_sender_email=env("ses_sender_email")

elasticsearch_username=env("elasticsearch_username")
elasticsearch_password=env("elasticsearch_password")
elasticsearch_cloud_id=env("elasticsearch_cloud_id")
