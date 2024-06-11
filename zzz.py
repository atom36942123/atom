#ec2
path = sudo -i / cd atom/atom
code pull = git pull origin main
server starts = sh /opt/fastapi.sh
edit file = nano .env

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
