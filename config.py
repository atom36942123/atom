#env
from environs import Env
env=Env()
env.read_env()

postgres_database_url=env("postgres_database_url")
redis_server_url=env("redis_server_url")
mongo_server_url=env("mongo_server_url")
sentry_dsn=env("sentry_dsn")
jwt_secret_key=env("jwt_secret_key")

elasticsearch_username=env("elasticsearch_username")
elasticsearch_password=env("elasticsearch_password")
elasticsearch_cloud_id=env("elasticsearch_cloud_id")

sns_region=env("sns_region")
sns_access_key_id=env("sns_access_key_id")
sns_secret_access_key=env("sns_secret_access_key")

ses_region=env("ses_region")
ses_access_key_id=env("ses_access_key_id")
ses_secret_access_key=env("ses_secret_access_key")
ses_email=env("ses_email")

s3_region=env("s3_region")
s3_access_key_id=env("s3_access_key_id")
s3_secret_access_key=env("s3_secret_access_key")
s3_bucket_name=env("s3_bucket_name")

rekognition_region=env("rekognition_region")
rekognition_access_key_id=env("rekognition_access_key_id")
rekognition_secret_access_key=env("rekognition_secret_access_key")
