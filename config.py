#env read
import os
from dotenv import load_dotenv
load_dotenv()

#env variables
redis_server_url=os.getenv("redis_server_url")
postgres_database_url=os.getenv("postgres_database_url")
secret_key_jwt=os.getenv("secret_key_jwt")
secret_key_root=os.getenv("secret_key_root")
sentry_dsn=os.getenv("sentry_dsn")
secret_key_openai=os.getenv("secret_key_openai")
sns_region_name=os.getenv("sns_region_name")
sns_access_key_id=os.getenv("sns_access_key_id")
sns_secret_access_key=os.getenv("sns_secret_access_key")
ses_region_name=os.getenv("ses_region_name")
ses_access_key_id=os.getenv("ses_access_key_id")
ses_secret_access_key=os.getenv("ses_secret_access_key")
s3_access_key_id=os.getenv("s3_access_key_id")
s3_secret_access_key=os.getenv("s3_secret_access_key")
rekognition_region_name=os.getenv("rekognition_region_name")
rekognition_access_key_id=os.getenv("rekognition_access_key_id")
rekognition_secret_access_key=os.getenv("rekognition_secret_access_key")