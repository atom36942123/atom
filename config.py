#env
from environs import Env
env=Env()
env.read_env()

#backend
config_backend_host=env("backend_host")
config_backend_port=env.int("backend_port")

#url
config_redis_url=env("redis_url")
config_mongo_url=env("mongo_url")
config_postgres_instance=env("postgres_instance")

#aws
config_aws_access_key_id=env("aws_access_key_id")
config_aws_secret_access_key=env("aws_secret_access_key")
config_aws_s3_bucket_region=env("aws_s3_bucket_region")
config_aws_s3_bucket_name=env("aws_s3_bucket_name")
config_aws_ses_region=env("aws_ses_region")
config_aws_ses_sender=env("aws_ses_sender")

#elasticsearch
config_elasticsearch_cloud_id=env("elasticsearch_cloud_id")
config_elasticsearch_username=env("elasticsearch_username")
config_elasticsearch_password=env("elasticsearch_password")

#misc
config_jwt_secret_key=env("jwt_secret_key")
config_jwt_expire_day=env.int("jwt_expire_day")
config_token_root=env("token_root")
config_x=env.list("x")
