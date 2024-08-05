#env read
from environs import Env
env=Env()
env.read_env()

#env unpack
config_postgres_url=env("postgres_url")
config_key=env("key")
config_key_jwt=env("key_jwt")
config_aws_access_key_id=env("aws_access_key_id")
config_aws_secret_access_key=env("aws_secret_access_key")
config_s3_bucket=env("s3_bucket")
config_s3_region=env("s3_region")
config_ses_sender=env("ses_sender")
config_ses_region=env("ses_region")
config_redis_url=env("redis_url")

#postgres object
from databases import Database
postgres_object={item.split("/")[-1]:Database(item,min_size=1,max_size=100) for item in config_postgres_url.split(",")}


