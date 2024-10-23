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
aws_access_key_id=os.getenv("aws_access_key_id")
aws_secret_access_key=os.getenv("aws_secret_access_key")

