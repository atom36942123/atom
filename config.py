#env
from environs import Env
env=Env()
env.read_env()
config_postgres_database_url=env("config_postgres_database_url")
config_redis_server=env("config_redis_server")
config_mongo_server=env("config_mongo_server")
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

#postgres object
from databases import Database
postgres_object=Database(config_postgres_database_url,min_size=1,max_size=100)

#database
config_database_extension=["postgis"]
config_database_table=["users","post","box","atom","likes","bookmark","report","block","rating","comment","message","helpdesk","otp","log"]
config_database_column={
"id":["bigint",config_database_table],
"created_at":["timestamptz",config_database_table],
"created_by_id":["bigint",config_database_table],
"updated_at":["timestamptz",["users","post","box","atom","report","comment","message","helpdesk"]],
"updated_by_id":["bigint",["users","post","box","atom","report","comment","message","helpdesk"]],
"is_active":["int",["users","post"]],
"is_verified":["int",["users","post"]],
"is_protected":["int",["users","post","box","atom"]],
"parent_table":["text",["likes","bookmark","report","block","rating","comment","message"]],
"parent_id":["bigint",["likes","bookmark","report","block","rating","comment","message"]],
"type":["text",["users","post","box","atom","helpdesk"]],
"status":["text",["report","helpdesk","message"]],
"remark":["text",["report","helpdesk"]],
"rating":["numeric",["rating","atom","post"]],
"metadata":["jsonb",["users","post","box","atom"]],
"username":["text",["users"]],
"password":["text",["users"]],
"google_id":["text",["users"]],
"profile_pic_url":["text",["users"]],
"last_active_at":["timestamptz",["users"]],
"name":["text",["users"]],
"email":["text",["users","post","box","atom","otp","helpdesk"]],
"mobile":["text",["users","post","box","atom","otp","helpdesk"]],
"date_of_birth":["date",["users"]],
"title":["text",["users","post","box","atom"]],
"description":["text",["users","post","box","atom","report","block","comment","message","helpdesk"]],
"file_url":["text",["post","box","atom","comment","message"]],
"link_url":["text",["post","box","atom"]],
"tag":["text",["users","post","box","atom"]],
"otp":["int",["otp"]],
"tag_array":["text[]",["atom"]],
"location":["geography(POINT)",["users","post","box","atom"]],
"request_path":["text",["log"]],
"request_query_param":["jsonb",["log"]],
"request_body":["jsonb",["log"]],
}
config_database_index={
"id":"btree",
"created_at":"brin",
"is_verified":"btree",
"is_active":"btree",
"parent_table":"btree",
"parent_id":"btree",
"type":"btree",
"created_by_id":"btree",
"status":"btree",
"email":"btree",
"password":"btree",
"location":"gist",
"tag":"btree",
"tag_array":"gin",
}
config_database_not_null={
"id":config_database_table,
"created_at":config_database_table,
"parent_table":["likes","bookmark","report","block","rating","comment","message"],
"parent_id":["likes","bookmark","report","block","rating","comment","message"]
}
config_database_identity={
"id":config_database_table
}
config_database_default={
"created_at":["now()",config_database_table]
}
config_database_unique={
"username":["users"],
"created_by_id,parent_table,parent_id":["likes","bookmark","report","block"]
}
config_database_query=[
"insert into users (username,password,type,is_protected) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','admin',1) on conflict do nothing;",
"create or replace rule rule_delete_disable_root_user as on delete to users where old.id=1 do instead nothing;",
"CREATE OR REPLACE FUNCTION function_set_updated_at_now() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ language 'plpgsql';",
"CREATE OR REPLACE VIEW view_table_master AS with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),y as (select table_name,count(*) as count_column from information_schema.columns group by table_name) select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;",
"CREATE OR REPLACE VIEW view_column_master AS select column_name,count(*),max(data_type) as datatype,max(udt_name) as udt_name from information_schema.columns where table_schema='public' group by  column_name order by count desc;",
"create materialized view if not exists mat_table_object_count as select relname as table_name,n_live_tup as count_object from pg_stat_user_tables order by count_object desc",
]
