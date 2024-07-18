#env
from environs import Env
env=Env()
env.read_env()

#aws
config_aws_access_key_id=env("aws_access_key_id")
config_aws_secret_access_key=env("aws_secret_access_key")
config_aws_s3_bucket_region=env("aws_s3_bucket_region")
config_aws_s3_bucket_name=env("aws_s3_bucket_name")
config_aws_ses_region=env("aws_ses_region")
config_aws_ses_sender=env("aws_ses_sender")

#misc
config_jwt_secret_key=env("jwt_secret_key")
config_token_root=env("token_root")

