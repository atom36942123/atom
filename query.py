query_schema_column="select * from information_schema.columns where table_schema='public';"
query_schema_constraint="select constraint_name from information_schema.constraint_column_usage;"
query_create_root_user="insert into users (username,password,type) values ('root','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3','root') on conflict do nothing returning *;"
query_rule_delete_disable_users_root="create or replace rule rule_delete_disable_users_root as on delete to users where old.id=1 or old.type='root' do instead nothing;"


