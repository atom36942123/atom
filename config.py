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
sns_access_key_id=env("access_key_id")
sns_secret_access_key=env("secret_access_key")





