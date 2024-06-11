#drop all
DO $$ DECLARE r RECORD;
BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname=current_schema()) LOOP
EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; 
END LOOP;
END $$;

#table info
with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),
y as (select table_name,count(*) as count_column from information_schema.columns group by table_name)
select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;

#exim
import_full=\copy post from 'path' with (format csv,header);
import_column=\copy post(xxx,yyy) from 'path' with (format csv,header);
export_full=\copy post to 'filename' with (format csv,header);
export_column=\copy (query)  to 'filename' with (format csv,header);

#info
info_db=SELECT datname FROM pg_database WHERE datistemplate=false;
info_table=SELECT * FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';
info_column=select * from information_schema.columns where table_schema='public';
info_constraints=select constraint_name from information_schema.constraint_column_usage;
info_index=select * from pg_indexes where schemaname='public'

#query
jsonb_text_read=select * from post where jsonb_1::text like '%neo%';
tag_one_read=select * from post where 'investor'=any(tag);
tag_many_any_read=select * from post where tag && '{"news","ai"}';
tag_many_all_read=select * from post where tag @> '{"news","ai"}';
tag_regex_read=select * from post where (array_to_string(tag,'')~*'funding news')
tag_append_duplicate=update box set tag=array_append(tag,'designation') where id=5455;
tag_append_duplicate_not=update box set tag=(select array_agg(distinct t) from unnest(tag||'{xxx}') as t) where id=1;
tag_append_position=update post set tag='news'::text||tag[1:] where type='acquisition';
tag_remove_one=update box set tag=array_remove(tag,'atom');
tag_replace=update post set tag=array_replace(tag,'meme','memes')

#connection kill
select pg_terminate_backend(pid) from pg_stat_activity 
where 
-- don't kill my own connection!
pid <> pg_backend_pid()
-- don't kill the connections to other databases
and datname='database_name';

#ec2
path = sudo -i / cd atom/atom
code pull = git pull origin main
server starts = sh /opt/fastapi.sh
edit file = nano .env

#postgres
install=brew install postgresql
start=brew services start postgresql
stop=brew services stop postgresql
restart=brew services restart postgresql
login=psql postgres ritu

#redis
install=brew install redis
start=brew services start redis
stop=brew services stop redis
info=brew services info redis
running=redis-cli ping

#mongo
start=brew services start mongodb-community
stop=brew services stop mongodb-community

#env
create=python -m venv atom
activate= source atom/bin/activate
freeze=pip freeze > requirement.txt
install=pip install -r requirement.txt --ignore-installed PyYAML

#jupyter
create env=conda create --name ml
activate env=conda activate ml
delete=conda remove -n ml --all
start=jupyter notebook

#kill pid
lsof -i:8000
kill -9 44511

#update	requirement
1. pip-review
2. pip-review --auto 
3. pip freeze > requirement.txt
4. pip install -r requirement.txt
5. if 3rd step - no error - gut push
6. else reduce version of red ones in requirement.txt and run again step 4 till error is zero
7. <pip install -r requirement.txt> on server

#retool api trigger
await create_s3_url.trigger({
  onSuccess:function(data) {
  upload_s3_url.trigger({
  onSuccess:function(data) {
  localStorage.setValue( "s3_url", (create_s3_url.data.message.url + create_s3_url.data.message.fields.key)  );
  }})
}})

#postman if/else
#if
postman.setEnvironmentVariable("x","xxx");
if (pm.environment.name=="prod")
{ postman.setEnvironmentVariable("x","yyy");
}

#logout javascript
var logout_days=30
//logic
if (localStorage.values.login_time!=null){
  var login_time=localStorage.values.login_time;
  var now=moment().unix();
  var ageing_days=(now-login_time)/86400;
  if (ageing_days > logout_days ){logout.trigger();} 
}

#object key into list
const post_tag= {{localStorage.values.project_cache.post_tag}}
const post_tag_list=post_tag.map(v=>v.tag)
return post_tag_list

#linux
rm <file_name>
rm -r <folder_name>
