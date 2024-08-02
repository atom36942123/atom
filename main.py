#useful
#aws=sudo -i / cd atom/atom / git pull origin main / sh /opt/fastapi.sh
# export=\copy post to 'filename' with (format csv,header);
# import=\copy post from 'path' with (format csv,header);
# export_column=\copy (query)  to 'filename' with (format csv,header);
# import_column=\copy post(type,title,description,link,tag) from /root/atom/atom/post.csv with (format csv,header);
# tag_read_one=select * from post where 'investor'=any(tag);
# tag_read_all=select * from post where tag @> '{"xxx","yyy"}';
# tag_read_any=select * from post where tag && '{"xxx","yyy"}';
# tag_read_regex=select * from post where (array_to_string(tag,'')~*'xx');
# tag_replace=update post set tag=array_replace(tag,'xxx','yyy')
# tag_append=update box set tag=array_append(tag,'xxx') where id=1;
# tag_append_no_duplicate=update box set tag=(select array_agg(distinct t) from unnest(tag||'{xxx}') as t) where id=1;
# tag_delete=update box set tag=array_remove(tag,'atom') where id=1;
#redis_size=redis-cli info memory | grep 'used_memory.*human';
#postgres=brew install postgresql@16 / brew services start postgresql@16 / psql postgres
#redis=brew install redis / brew services start redis
#pgweb=brew install pgweb / pgweb --url postgresql://localhost:5432/postgres

#s3 upload
# curl --location 'https://atom36942-production.s3.amazonaws.com/' \
# --form 'key="xxx"' \
# --form 'policy="xxx"' \
# --form 'x-amz-date="xxx"' \
# --form 'x-amz-algorithm="xxx"' \
# --form 'x-amz-credential="xxx"' \
# --form 'x-amz-signature="xxx"' \
# --form 'file=@"9w4PMnK0L/logo atom.jpg"'

#body
#csv={"file":atom_create.csv}
#csv={"file":atom_update.csv}
#csv={"file":atom_delete.csv}
#feed={table:post,page:1,limit:100,id:100,id_operator:>=,order:created_by_id desc}
#signup={"username":"xxx","password":"123"}
#login={"username":"xxx","password":"123"}
#create={"table":"post","type":"xxx","description":"xxx"}
#create={"table":"action","type":"report","parent_table":"post","parent_id":1,"description":"xxx"}
#create={"table":"activity","type":"message","parent_table":"users","parent_id":2,"description":"xxx"}
#create={"table":"action","type":"like","parent_table":"post","parent_id":4}
#create={"table":"activity","type":"comment","parent_table":"post","parent_id":4,"description":"xxx"}
#update={"table":"users","id":1,"name":"xxx"}
#delete={"table":"post","id":7012}
#read={"table":"post", "id":1,"id_operator":">","page":1,"limit":1}
#my={"mode":"message_inbox"}
#my={"mode":"message_inbox_unread"}
#my={"mode":"message_thread","user_id":2}
#my={"mode":"message_received"}
#my={"mode":"delete_message_all"}
#my={"mode":"read_parent_data","table":"action","type":"like","parent_table":"post"}
#my={"mode":"read_parent_data","table":"activity","type":"report","parent_table":"post"}
#my={"mode":"action_check","table":"action","type":"like","parent_table":"post","ids":[1,2,3]}
#my={"mode":"action_check","table":"activity","type":"report","parent_table":"post","ids":[1,2,3]}
#admin={"mode":"update_cell","table":"users","id":1,"column":"type","value":"admin"}
#aws={"mode":"s3_create","filename":"abc.png"}
#aws={"mode":"s3_delete","url":"www.abc.png/23123"}
#aws={"mode":"s3_delete_all"}
#aws={"mode":"ses","email":"atom36942@gmail.com","title":"hello","description":"hello"}
#mongo={"mode":"create"}|{user object}
#mongo={"mode":"read","id":user_id}
#mongo={"mode":"update","id":user_id}|{user object}
#mongo={"mode":"read","id":user_id}
#elasticsearch={"mode":"create","table":"users"}|{object}
#elasticsearch={"mode":"read","table":"users","id":user_id}
#elasticsearch={"mode":"update","table":"users","id":user_id}|{object}
#elasticsearch={"mode":"delete","table":"users","id":user_id}
#elasticsearch={"mode":"refresh","table":"users"}
#elasticsearch={"mode":"search","table":"users","keyword":"xxx","size":30}

#package
package="pip install a==1.0 aiohttp==3.9.1 aiosignal==1.3.1 annotated-types==0.6.0 anyio==4.3.0 appnope==0.1.4 APScheduler==3.10.4 argon2-cffi==23.1.0 argon2-cffi-bindings==21.2.0 arrow==1.3.0 asgiref==3.7.2 asttokens==2.4.1 async-lru==2.0.4 async-timeout==4.0.3 asyncpg==0.29.0 attrs==23.2.0 autocommand==2.2.2 Automat==0.8.0 awscli==1.18.69 Babel==2.14.0 beautifulsoup4==4.12.3 bleach==6.1.0 blinker==1.4 boto3==1.34.49 botocore==1.34.17 certifi==2023.11.17 cffi==1.16.0 chardet==3.0.4 charset-normalizer==3.3.2 cheroot==10.0.0 CherryPy==18.9.0 click==8.1.7 cloud-init==24.1.3 colorama==0.4.6 comm==0.2.1 commonmark==0.9.1 configobj==5.0.6 constantly==15.1.0 cryptography==41.0.7 databases==0.8.0 dbus-python==1.2.16 debugpy==1.8.1 decorator==5.1.1 defusedxml==0.7.1 Deprecated==1.2.14 distlib==0.3.8 distro==1.4.0 distro-info==0.23+ubuntu1.1 dnspython==2.4.2 docutils==0.16 ec2-hibinit-agent==1.0.0 elastic-transport==8.13.0 elasticsearch==8.13.0 entrypoints==0.3 environs==10.3.0 executing==2.0.1 fastapi==0.110.0 fastapi-cache2==0.2.1 fastapi-limiter==0.1.6 fastjsonschema==2.19.1 fqdn==1.5.1 frozenlist==1.4.1 gazpacho==1.1 greenlet==3.0.3 h11==0.14.0 hibagent==1.0.1 httpcore==1.0.4 httplib2==0.14.0 httpx==0.27.0 hyperlink==19.0.0 idna==3.6 importlib-metadata==1.5.0 incremental==16.10.1 inflect==7.0.0 install==1.3.5 ipykernel==6.29.2 ipython==8.22.1 isoduration==20.11.0 jaraco.classes==3.3.0 jaraco.collections==5.0.0 jaraco.context==4.3.0 jaraco.functools==4.0.0 jaraco.text==3.12.0 jedi==0.19.1 Jinja2==3.1.3 jmespath==1.0.1 json5==0.9.17 jsonpatch==1.22 jsonpointer==2.4 jsonschema==4.21.1 jsonschema-specifications==2023.12.1 jupyter-events==0.9.0 jupyter-lsp==2.2.2 jupyter_client==8.6.0 jupyter_core==5.7.1 jupyter_server==2.12.5 jupyter_server_terminals==0.5.2 jupyterlab==4.1.2 jupyterlab_pygments==0.3.0 jupyterlab_server==2.25.3 keyring==18.0.1 launchpadlib==1.10.13 lazr.restfulclient==0.14.2 lazr.uri==1.0.3 markdown-it-py==3.0.0 MarkupSafe==2.1.5 marshmallow==3.20.2 matplotlib-inline==0.1.6 mdurl==0.1.2 mistune==3.0.2 more-itertools==10.2.0 motor==3.3.2 multidict==6.0.5 nbclient==0.9.0 nbconvert==7.16.1 nbformat==5.9.2 nest-asyncio==1.6.0 netifaces==0.10.4 notebook==7.1.0 notebook_shim==0.2.4 numpy==1.26.3 oauthlib==3.1.0 of==1.0.1 olefile==0.46 overrides==7.7.0 packaging==23.2 pandas==2.1.4 pandocfilters==1.5.1 parso==0.8.3 pendulum==3.0.0 pexpect==4.9.0 Pillow==7.0.0 pip-review==1.3.0 platformdirs==4.2.0 portend==3.2.0 prometheus_client==0.20.0 prompt-toolkit==3.0.43 psutil==5.9.8 ptyprocess==0.7.0 pure-eval==0.2.2 pyasn1-modules==0.2.1 pycparser==2.21 pydantic==2.5.3 pydantic_core==2.14.6 Pygments==2.17.2 PyGObject==3.36.0 PyJWT==2.8.0 pymacaroons==0.13.0 pymongo==4.6.1 pyparsing==3.1.1 pyrsistent==0.20.0 python-apt==2.0.1+ubuntu0.20.4.1 python-dateutil==2.8.2 python-debian==0.1.36+ubuntu1.1 python-dotenv==1.0.1 python-json-logger==2.0.7 python-multipart==0.0.9 pytz==2024.1 pytz-deprecation-shim==0.1.0.post0 pytzdata==2020.1 PyYAML==6.0.1 pyzmq==25.1.2 redis==5.1.0b2 referencing==0.33.0 requests==2.31.0 rfc3339-validator==0.1.4 rfc3986-validator==0.1.1 rich==13.7.0 roman==2.0.0 rpds-py==0.18.0 s3transfer==0.10.0 SecretStorage==2.3.1 Send2Trash==1.8.2 shellingham==1.5.4 simplejson==3.16.0 six==1.16.0 sniffio==1.3.0 sos==4.5.6 soupsieve==2.5 SQLAlchemy==1.4.51 stack-data==0.6.3 starlette==0.35.1 systemd-python==234 tempora==5.5.1 terminado==0.18.0 time-machine==2.13.0 tinycss2==1.2.1 to==0.3 tornado==6.4 traitlets==5.14.1 Twisted==18.9.0 typer==0.9.0 types-python-dateutil==2.8.19.20240106 typing_extensions==4.9.0 tzdata==2024.1 tzlocal==5.2 ufw==0.36 uri-template==1.3.0 urllib3==2.0.7 uvicorn==0.27.1 wcwidth==0.2.13 webcolors==1.13 webencodings==0.5.1 websocket-client==1.7.0 wrapt==1.16.0 ws4py==0.5.1 yarl==1.9.4 zc.lockfile==3.0.post1 zipp==1.0.0"

#env
from environs import Env
env=Env()
env.read_env()
postgres_url_list=env.list("postgres")
key=env("key")
aws_access_key_id,aws_secret_access_key=env.list("aws")[0],env.list("aws")[1]
s3_bucket,s3_region=env.list("s3")[0],env.list("s3")[1]
ses_sender,ses_region=env.list("ses")[0],env.list("ses")[1]

#database
from databases import Database
postgres_object={item.split("/")[-1]:Database(item,min_size=1,max_size=100) for item in postgres_url_list}

#lifespan
from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
@asynccontextmanager
async def lifespan(app:FastAPI):
   #redis
   redis_object=aioredis.from_url("redis://127.0.0.1",encoding="utf-8",decode_responses=True)
   await FastAPILimiter.init(redis_object)
   FastAPICache.init(RedisBackend(redis_object))
   #postgres
   for k,v in postgres_object.items():await v.connect()
   #shutdown
   yield 
   for k,v in postgres_object.items():await v.disconnect()

#app
from fastapi import FastAPI
app=FastAPI(lifespan=lifespan,title="atom")

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#middleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback
@app.middleware("http")
async def middleware(request:Request,api_function):
   #x check
   x=str(request.url).split("/")[3]
   if x not in ["","docs","redoc","openapi.json"]+[*postgres_object]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"wrong x"}))
   #database assgin
   if x in postgres_object:request.state.postgres_object=postgres_object[x]
   #api response
   try:response=await api_function(request)
   except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":e.args}))
   #except Exception as e:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":traceback.format_exc()}))
   #final
   return response

#api import
from fastapi import Request,Response,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs,jwt,time,boto3,uuid
from datetime import datetime,timedelta
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch

#api
@app.get("/")
async def function_root():
   return {"status":1,"message":f"welcome to {[*postgres_object]}"}

@app.get("/{x}/qrunner")
async def function_qrunner(request:Request,query:str):
   #prework
   database=request.state.postgres_object.fetch_all
   if request.headers.get("token")!=key:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #mapping
   mapping={
   "reset":"DO $$ DECLARE r RECORD; BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname=current_schema()) LOOP EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; END LOOP; END $$;",
   "database":"select * from pg_database where datistemplate=false;",
   "constraint":"select * from information_schema.constraint_column_usage;",
   "index":"select * from pg_indexes where schemaname='public';",
   "rules":"select * from pg_rules;",
   "table":"select * from information_schema.tables where table_schema='public' and table_type='BASE TABLE';",
   "column":"select * from information_schema.columns where table_schema='public';",
   "tableg":"with x as (select relname as table_name,n_live_tup as count_row from pg_stat_user_tables),y as (select table_name,count(*) as count_column from information_schema.columns group by table_name) select x.*,y.count_column from x left join y on x.table_name=y.table_name order by count_column desc;",
   "columng":"select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;",
   }
   if query in mapping:query=mapping[query]
   #logic
   query=query
   values={}
   output=await database(query=query,values=values)
   #final
   return output
    
@app.get("/{x}/database")
async def function_database(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   if request.headers.get("token")!=key:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #config
   config_database={
   "created_at":["timestamptz","users,post,action,activity,box,atom"],
   "created_by_id":["bigint","users,post,action,activity,box,atom"],
   "updated_at":["timestamptz","users,post,action,activity,box,atom"],
   "updated_by_id":["bigint","users,post,action,activity,box,atom"],
   "is_active":["int","users,post,action,activity,box,atom"],
   "is_verified":["int","users,post,action,activity,box,atom"],
   "is_protected":["int","users,post,action,activity,box,atom"],
   "type":["text","users,post,action,activity,box,atom"],
   "status":["text","users,post,action,activity,box,atom"],
   "remark":["text","users,post,action,activity,box,atom"],
   "metadata":["jsonb","users,post,action,activity,box,atom"],
   "parent_table":["text","action,activity"],
   "parent_id":["bigint","action,activity"],
   "last_active_at":["timestamptz","users"],
   "google_id":["text","users"],
   "otp":["int","box"],
   "username":["text","users"],
   "password":["text","users"],
   "name":["text","users"],
   "email":["text","users,post,box,atom"],
   "mobile":["text","users,post,box,atom"],
   "title":["text","users,post,box,atom"],
   "description":["text","users,post,action,activity,box,atom"],
   "tag":["text","users,post,box,atom"],
   "link":["text","users,post,box,atom"],
   "file":["text","users,post,box,atom"],
   "rating":["numeric","users,post,box,atom"],
   }
   #create table
   table_all=config_database["created_at"][1].split(',')
   for table in table_all:
      query=f"create table if not exists {table} (id bigint primary key generated always as identity);"
      values={}
      output=await database(query=query,values=values)
   #create column
   for k,v in config_database.items():
      for table in v[1].split(','):
         query=f"alter table {table} add column if not exists {k} {v[0]};"
         values={}
         output=await database(query=query,values=values)
   #created_at default
   for table in table_all:
      query=f"alter table {table} alter column created_at set default now();"
      values={}
      output=await database(query=query,values=values)
   #protected rows
   for table in config_database["is_protected"][1].split(','):
      query=f"create or replace rule rule_delete_disable_{table} as on delete to {table} where old.is_protected=1 do instead nothing;"
      values={}
      output=await database(query=query,values=values)
   #set not null
   mapping_not_null={"created_by_id":["action","activity"],"parent_table":["action","activity"],"parent_id":["action","activity"]}
   for k,v in mapping_not_null.items():
      for table in v:
         query=f"alter table {table} alter column {k} set not null;"
         values={}
         output=await database(query=query,values=values)
   #schema constraint
   query="select constraint_name from information_schema.constraint_column_usage;"
   values={}
   output=await database(query=query,values=values)
   schema_constraint_name_list=[item["constraint_name"] for item in output]
   #query zzz
   query_zzz=["alter table users add constraint constraint_unique_users unique (username);",
   "alter table action add constraint constraint_unique_action unique (type,created_by_id,parent_table,parent_id);"
   ]
   for item in query_zzz:
      if item.split()[5] not in schema_constraint_name_list:
         query=item
         values={}
         output=await database(query=query,values=values)
   #drop index
   query="select 'drop index ' || string_agg(i.indexrelid::regclass::text,', ' order by n.nspname,i.indrelid::regclass::text, cl.relname) as output from pg_index i join pg_class cl ON cl.oid = i.indexrelid join pg_namespace n ON n.oid = cl.relnamespace left join pg_constraint co ON co.conindid = i.indexrelid where  n.nspname <> 'information_schema' and n.nspname not like 'pg\_%' and co.conindid is null and not i.indisprimary and not i.indisunique and not i.indisexclusion and not i.indisclustered and not i.indisreplident;"
   values={}
   output=await database(query=query,values=values)
   if output[0]["output"]:
      query=output[0]["output"]
      values={}
      output=await database(query=query,values=values)
   #schema column
   query="select * from information_schema.columns where table_schema='public' order by column_name;"
   values={}
   schema_column=await database(query=query,values=values)
   #create index
   column_to_index=["type","is_verified","is_active","created_by_id","status","parent_table","parent_id","email","password","created_at"]
   mapping_index_datatype={"text":"btree","bigint":"btree","integer":"btree","numeric":"btree","timestamp with time zone":"brin","date":"brin","jsonb":"gin","ARRAY":"gin"}
   for column in schema_column:
      if column['column_name'] in column_to_index:
         query=f"create index if not exists index_{column['column_name']}_{column['table_name']} on {column['table_name']} using {mapping_index_datatype[column['data_type']]} ({column['column_name']});"
         values={}
         output=await database(query=query,values=values)
   #final
   return {"status":1,"message":"done"}
   
@app.post("/{x}/csv")
async def function_csv(request:Request,file:UploadFile):
   #prework
   database=request.state.postgres_object.fetch_all
   database_bulk=request.state.postgres_object.execute_many
   if request.headers.get("token")!=key:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   #schema column groupby
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await database(query=query,values=values)
   schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
   #file
   file_object=csv.DictReader(codecs.iterdecode(file.file,'utf-8'))
   file_column_list=file_object.fieldnames
   filename=file.filename.split(".")[0]
   table=filename.rsplit("_",1)[0]
   mode=filename.rsplit("_",1)[1]
   #body preprocessing
   values=[]
   for row in file_object:
      for column in file_column_list:
         if column not in schema_column_datatype:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"column not in the schema"}))
         if column in ["password","google_id"]:row[column]=hashlib.sha256(row[column].encode()).hexdigest() if row[column] else None  
         if schema_column_datatype[column] in ["jsonb"]:row[column]=json.dumps(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["ARRAY"]:row[column]=row[column].split(",") if row[column] else None
         if schema_column_datatype[column] in ["integer","bigint"]:row[column]=int(row[column]) if row[column] else None
         if schema_column_datatype[column] in ["decimal","numeric","real","double precision"]:row[column]=round(float(row[column]),3) if row[column] else None
         if schema_column_datatype[column] in ["date","timestamp with time zone"]:row[column]=datetime.strptime(row[column],'%Y-%m-%d') if row[column] else None
      values.append(row)
   file.file.close
   #query set
   if mode=="create":
      column_1=','.join(file_column_list)
      column_2=','.join([':'+item for item in file_column_list])
      query=f"insert into {table} ({column_1}) values ({column_2}) returning *;"
      values=values
   if mode=="update":
      param=[item for item in file_column_list if item not in ["id"]]
      column=""
      for k in param:column=column+f"{k}=coalesce(:{k},{k}),"
      column=column[:-1]
      query=f"update {table} set {column} where id=:id returning *;"
      values=values
   if mode=="delete":
      query=f"delete from {table} where id=:id;"
      values=values
   #query run
   output=await database_bulk(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.get("/{x}/clean")
async def function_clean(request:Request):
   #prewrok
   database=request.state.postgres_object.fetch_all
   #created_by_id null
   for table in ["post","action","activity"]:
      query=f"delete from {table} where created_by_id not in (select id from users);"
      values={}
      output=await database(query=query,values=values)
   #parent_id null
   for table in ["action","activity"]:
      for parent_table in ["users","post","activity"]:
         query=f"delete from {table} where parent_table='{parent_table}' and parent_id not in (select id from {parent_table});"
         values={}
         output=await database(query=query,values=values)
   #final
   return {"status":1,"message":"done"}

@app.get("/{x}/pcache")
@cache(expire=60)
async def function_pcache(request:Request):
   #prewrok
   database=request.state.postgres_object.fetch_all
   temp={}
   query_dict={"user_count":"select count(*) from users;"}
   #logic
   for k,v in query_dict.items():
      query=v
      values={}
      output=await database(query=query,values=values)
      temp[k]=output
   #final
   return {"status":1,"message":temp}

def function_redis_key_builder(func,namespace:str="",*,request:Request=None,response:Response=None,**kwargs):return ":".join([namespace,request.method.lower(),request.url.path,repr(sorted(request.query_params.items()))])
@app.get("/{x}/feed")
@cache(expire=60,key_builder=function_redis_key_builder)
async def function_feed(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   body=dict(request.query_params)
   #schema column groupby
   query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
   values={}
   output=await database(query=query,values=values)
   schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
   #body preprocessing
   for k,v in body.items():
      if k in schema_column_datatype:
         if schema_column_datatype[k] in ["ARRAY"]:body[k]=v.split(",")
         if schema_column_datatype[k] in ["integer","bigint"]:body[k]=int(v)
         if schema_column_datatype[k] in ["decimal","numeric","real","double precision"]:body[k]=float(v)
   #query set
   table=body["table"]
   where=""
   order=body["order"] if "order" in body else "id desc"
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #param set
   param={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
   if param:
      where="where "
      for k,v in param.items():
         if f"{k}_operator" in body:where=where+f"({k}{body[f'{k}_operator']}:{k} or :{k} is null) and "
         else:where=where+f"({k}=:{k} or :{k} is null) and "
      where=where.strip().rsplit('and',1)[0]
   #query run
   query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
   values=param
   output=await database(query=query,values=values)
   output=[dict(item) for item in output]
   #add creator key
   object_list=output
   object_table=table
   if object_list and object_table in ["post"]:
      object_list=[item|{"created_by_username":None} for item in object_list]
      user_ids=','.join([str(item["created_by_id"]) for item in object_list if item["created_by_id"]])
      if user_ids:
         query=f"select * from users where id in ({user_ids});"
         values={}
         object_user_list=await database(query=query,values=values)
         for object in object_list:
            for object_user in object_user_list:
               if object["created_by_id"]==object_user["id"]:
                  object["created_by_username"]=object_user["username"]
                  break
   #add action count
   object_list=object_list
   object_table=table
   action_type="comment"
   action_table="activity"
   key_name=f"{action_type}_count"
   if object_list and object_table in ["post"]:
      object_list=[item|{key_name:0} for item in object_list]
      parent_ids=list(set([item["id"] for item in object_list if item["id"]]))
      if parent_ids:
         query=f"select parent_id,count(*) from {action_table} join unnest(array{parent_ids}::int[]) with ordinality t(parent_id, ord) using (parent_id) where type=:type and parent_table=:parent_table group by parent_id;"
         values={"type":action_type,"parent_table":object_table}
         object_action_list=await database(query=query,values=values)
         for object in object_list:
            for object_action in object_action_list:
               if object["id"]==object_action["parent_id"]:
                  object[key_name]=object_action["count"]
                  break
   #final
   return {"status":1,"message":object_list}
   
@app.post("/{x}/signup",dependencies=[Depends(RateLimiter(times=1,seconds=5))])
async def function_signup(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   body=await request.json()
   #logic
   query="insert into users (username,password) values (:username,:password) returning *;"
   values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
   output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/{x}/login")
async def function_login(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   body=await request.json()
   #username
   if "mode" not in body:
      query="select * from users where username=:username and password=:password order by id desc limit 1;"
      values={"username":body["username"],"password":hashlib.sha256(body["password"].encode()).hexdigest()}
      output=await database(query=query,values=values)
      user=output[0] if output else None
      if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   #google
   if "mode" in body and body["mode"]=="google":
      query="select * from users where google_id=:google_id order by id desc limit 1;"
      values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()}
      output=await database(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (google_id) values (:google_id) returning *;"
         values={"google_id":hashlib.sha256(body["google_id"].encode()).hexdigest()}
         output=await database(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await database(query=query,values=values)
         user=output[0]
   #email
   if "mode" in body and body["mode"]=="email":
      query="select otp from box where type='otp' and email=:email order by id desc limit 1;"
      values={"email":body["email"]}
      output=await database(query=query,values=values)
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
      query="select * from users where email=:email order by id desc limit 1;"
      values={"email":body["email"]}
      output=await database(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (email) values (:email) returning *;"
         values={"email":body["email"]}
         output=await database(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await database(query=query,values=values)
         user=output[0]
   #mobile
   if "mode" in body and body["mode"]=="mobile":
      query="select otp from box where type='otp' and mobile=:mobile order by id desc limit 1;"
      values={"mobile":body["mobile"]}
      output=await database(query=query,values=values)
      if not output:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp not exist"}))
      if output[0]["otp"]!=body["otp"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"otp mismatched"}))
      query="select * from users where mobile=:mobile order by id desc limit 1;"
      values={"mobile":body["mobile"]}
      output=await database(query=query,values=values)
      user=output[0] if output else None
      if not user:
         query="insert into users (mobile) values (:mobile) returning *;"
         values={"mobile":body["mobile"]}
         output=await database(query=query,values=values)
         user_id=output[0]["id"]
         query="select * from users where id=:id;"
         values={"id":user_id}
         output=await database(query=query,values=values)
         user=output[0]
   #token encode
   expiry_days=1
   data=json.dumps({"x":str(request.url).split("/")[3],"created_at_token":datetime.today().strftime('%Y-%m-%d'),"id":user["id"],"is_active":user["is_active"],"type":user["type"]},default=str)
   payload={"exp":time.mktime((datetime.now()+timedelta(days=expiry_days)).timetuple()),"data":data}
   token=jwt.encode(payload,key)
   #final
   return {"status":1,"message":token}
   
@app.get("/{x}/profile")
async def function_profile(request:Request,background:BackgroundTasks):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   #read user
   query="select * from users where id=:id;"
   values={"id":user["id"]}
   output=await database(query=query,values=values)
   user=output[0] if output else None
   if not user:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"no user"}))
   user=dict(user)
   #count key
   query_dict={
   "post_count":"select count(*) from post where created_by_id=:user_id;",
   "comment_count":"select count(*) from activity where type='comment' and created_by_id=:user_id;",
   "message_unread_count":"select count(*) from activity where type='message' and parent_table='users' and parent_id=:user_id and status is null;"
   }
   for k,v in query_dict.items():
      query=v
      values={"user_id":user["id"]}
      output=await database(query=query,values=values)
      user[k]=output[0]["count"]
   #background task
   query="update users set last_active_at=:last_active_at where id=:id;"
   values={"last_active_at":datetime.now(),"id":user["id"]}
   background.add_task(await database(query=query,values=values))
   #final
   return {"status":1,"message":user}

@app.post("/{x}/create")
async def function_create(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] not in ["post","action","activity","box"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body preprocessing
   body["created_by_id"]=user["id"]
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   #query set
   table=body["table"]
   column_1=None
   column_2=None
   #param set
   param={k:v for k,v in body.items() if (k not in ["table"]+["id","created_at","is_active","is_verified","google_id","otp"] and v not in [None,""," "])}
   column_1=','.join([*param])
   column_2=','.join([':'+item for item in [*param]])
   #query run
   query=f"insert into {table} ({column_1}) values ({column_2}) returning *;"
   values=param
   output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/{x}/update")
async def function_update(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] not in ["users","post","action","activity","box"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body preprocessing
   body["updated_at"]=datetime.now()
   body["updated_by_id"]=user["id"]
   if "metadata" in body:body["metadata"]=json.dumps(body["metadata"],default=str)
   #query set
   table=body["table"]
   column=""
   id=user["id"] if table=="users" else body["id"]
   created_by_id=None if table=="users" else user["id"]
   #param set
   param={k:v for k,v in body.items() if (k not in ["table","id"]+["created_at","created_by_id","is_active","is_verified","type","google_id","otp","parent_table","parent_id"] and v not in [None,""," "])}
   for k,v in param.items():column=column+f"{k}=coalesce(:{k},{k}),"
   column=column[:-1]
   #query run
   query=f"update {table} set {column} where id=:id and (created_by_id=:created_by_id or :created_by_id is null) returning *;"
   values=param|{"id":id,"created_by_id":created_by_id}
   output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}
   
@app.post("/{x}/delete")
async def function_delete(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] not in ["users","post","action","activity"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #query set
   table=body["table"]
   id=user["id"] if table=="users" else body["id"]
   created_by_id=None if table=="users" else user["id"]
   #query run
   query=f"delete from {table} where id=:id and (created_by_id=:created_by_id or :created_by_id is null);"
   values={"id":id,"created_by_id":created_by_id}
   output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/{x}/read")
async def function_read(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   if body['table'] not in ["post","action","activity","box"]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"table not allowed"}))
   #body preprocessing
   body["created_by_id"]=user["id"]
   #query set
   table=body["table"]
   where=""
   order=body["order"] if "order" in body else "id desc"
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #param set
   param={k:v for k,v in body.items() if (k not in ["table","order","limit","page"] and "_operator" not in k and v not in [None,""," "])}
   if param:
      where="where "
      for k,v in param.items():
         if f"{k}_operator" in body:where=where+f"({k}{body[f'{k}_operator']}:{k} or :{k} is null) and "
         else:where=where+f"({k}=:{k} or :{k} is null) and "
      where=where.strip().rsplit('and',1)[0]
   #query run
   query=f"select * from {table} {where} order by {order} limit {limit} offset {offset};"
   values=param
   output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}
     
@app.post("/{x}/my")
async def function_my(request:Request,background:BackgroundTasks):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   body=await request.json()
   #pagination set
   limit=int(body["limit"]) if "limit" in body else 30
   page=int(body["page"]) if "page" in body else 1
   offset=(page-1)*limit
   #query set
   if body["mode"]=="message_inbox":
      query="with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id limit :limit offset :offset),y as (select a.* from x left join activity as a on x.id=a.id) select * from y order by id desc;"
      values={"created_by_id":user["id"],"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await database(query=query,values=values)
   if body["mode"]=="message_inbox_unread":
      query="with mcr as (select id,abs(created_by_id-parent_id) as unique_id from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id)),x as (select max(id) as id from mcr group by unique_id),y as (select a.* from x left join activity as a on x.id=a.id) select * from y where parent_id=:parent_id and status is null order by id desc limit :limit offset :offset;"
      values={"created_by_id":user["id"],"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await database(query=query,values=values)
   if body["mode"]=="message_thread":
      query="select * from activity where type='message' and parent_table='users' and ((created_by_id=:user_1 and parent_id=:user_2) or (created_by_id=:user_2 and parent_id=:user_1)) order by id desc limit :limit offset :offset;"
      values={"user_1":user["id"],"user_2":body["user_id"],"limit":limit,"offset":offset}
      output=await database(query=query,values=values)
   if body["mode"]=="message_received":
      query="select * from activity where type='message' and parent_table='users' and parent_id=:parent_id order by id desc limit :limit offset :offset;"
      values={"parent_id":user["id"],"limit":limit,"offset":offset}
      output=await database(query=query,values=values)
   if body["mode"]=="delete_message_all":
      query="delete from activity where type='message' and parent_table='users' and (created_by_id=:created_by_id or parent_id=:parent_id);"
      values={"created_by_id":user['id'],"parent_id":user['id']}
      output=await database(query=query,values=values)
   if body["mode"]=="read_parent_data":
      query=f"select parent_id from {body['table']} where created_by_id=:created_by_id and type=:type and parent_table=:parent_table order by id desc limit :limit offset :offset;"
      values={"created_by_id":user["id"],"type":body["type"],"parent_table":body["parent_table"],"limit":limit,"offset":offset}
      output=await database(query=query,values=values)
      parent_ids=[item["parent_id"] for item in output]
      query=f"select * from {body['parent_table']} join unnest(array{parent_ids}::int[]) with ordinality t(id, ord) using (id) order by t.ord;"
      values={}
      output=await database(query=query,values=values)
   if body["mode"]=="action_check":
      query=f"select parent_id from {body['table']} join unnest(array{body['ids']}::int[]) with ordinality t(parent_id, ord) using (parent_id) where created_by_id=:created_by_id and type=:type and parent_table=:parent_table;"
      values={"created_by_id":user["id"],"type":body["type"],"parent_table":body["parent_table"]}
      output=await database(query=query,values=values)
      output=list(set([item["parent_id"] for item in output if item["parent_id"]]))
   #background task
   if body["mode"]=="message_thread":
      query="update activity set status=:status,updated_by_id=:updated_by_id,updated_at=:updated_at where type='message' and parent_table='users' and created_by_id=:created_by_id and parent_id=:parent_id returning *;"
      values={"status":"read","created_by_id":body["user_id"],"parent_id":user["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      background.add_task(await database(query=query,values=values))
      output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/{x}/admin")
async def function_admin(request:Request):
   #prework
   database=request.state.postgres_object.fetch_all
   user=json.loads(jwt.decode(request.headers.get("token"),key,algorithms="HS256")["data"])
   if user["x"]!=str(request.url).split("/")[3]:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token x mismatch"}))
   if user["type"]!="admin":return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"admin issue"}))
   body=dict(await request.json())
   #logic
   if body["mode"]=="update_cell":
      #schema column groupby
      query="select column_name,count(*),max(data_type) as datatype from information_schema.columns where table_schema='public' group by  column_name order by count desc;"
      values={}
      output=await database(query=query,values=values)
      schema_column_datatype={item["column_name"]:item["datatype"] for item in output}
      #body preprocessing
      if body["column"] in ["password","google_id"]:body["value"]=hashlib.sha256(body["value"].encode()).hexdigest()
      if schema_column_datatype[body["column"]] in ["jsonb"]:body["value"]=json.dumps(body["value"])
      if schema_column_datatype[body["column"]] in ["ARRAY"]:body["value"]=body["value"].split(",")
      if schema_column_datatype[body["column"]] in ["integer","bigint"]:body["value"]=int(body["value"])
      if schema_column_datatype[body["column"]] in ["decimal","numeric","real","double precision"]:body["value"]=round(float(body["value"]),3)
      if schema_column_datatype[body["column"]] in ["date","timestamp with time zone"]:body["value"]=datetime.strptime(body["value"],'%Y-%m-%d')
      #logic
      query=f"update {body['table']} set {body['column']}=:value,updated_at=:updated_at,updated_by_id=:updated_by_id where id=:id returning *;"
      values={"value":body["value"],"id":body["id"],"updated_at":datetime.now(),"updated_by_id":user['id']}
      output=await database(query=query,values=values)
   #final
   return {"status":1,"message":output}

@app.post("/{x}/aws")
async def function_aws(request:Request):
   #prework
   body=await request.json()
   if request.headers.get("token")!=key:return JSONResponse(status_code=400,content=jsonable_encoder({"status":0,"message":"token issue"}))
   s3_client=boto3.client("s3",region_name=s3_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   ses_client=boto3.client("ses",region_name=ses_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   s3_resource=boto3.resource("s3",aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
   #logic
   if body["mode"]=="s3_create":
      expiry=1000
      size_kb=300
      bucket_key=str(uuid.uuid4())+"-"+body["filename"]
      output=s3_client.generate_presigned_post(Bucket=s3_bucket,Key=bucket_key,ExpiresIn=expiry,Conditions=[['content-length-range',1,size_kb*1024]])
   if body["mode"]=="s3_delete":
      bucket_key=body["url"].split("/")[-1]
      output=s3_resource.Object(s3_bucket,bucket_key).delete()
   if body["mode"]=="s3_delete_all":
      output=s3_resource.Bucket(s3_bucket).objects.all().delete()
   if body["mode"]=="ses":
      output=ses_client.send_email(Source=ses_sender,Destination={"ToAddresses":[body["email"]]},Message={"Subject":{"Charset":"UTF-8","Data":body["title"]},"Body":{"Text":{"Charset":"UTF-8","Data":body["description"]}}})
   #final
   return {"status":1,"message":output}

@app.post("/{x}/mongo")
async def function_mongo(request:Request):
   #prework
   body=await request.json()
   mongo_object=motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
   mode=body["mode"]
   body.pop("mode",None)
   #logic
   if mode=="create":
      response=await mongo_object.test.users.insert_one(body)
   if mode=="read":
      response=await mongo_object.test.users.find_one({"_id":ObjectId(body["id"])})
   if mode=="update":
      id=body["id"]
      body.pop("id",None)
      response=await mongo_object.test.users.update_one({"_id":ObjectId(id)},{"$set":body})
   if mode=="delete":
      response=await mongo_object.test.users.delete_one({"_id":ObjectId(body["id"])})
   #final
   return response

@app.post("/{x}/elasticsearch")
async def function_elasticsearch(request:Request,mode:str):
   #prework
   body=await request.json()
   elasticsearch_object=Elasticsearch(cloud_id=cloud_id,basic_auth=(username,password))
   mode=body["mode"]
   body.pop("mode",None)
   #table
   if "table" in body:
      table=body["table"]
      body.pop("table",None)
   #id
   if "id" in body:
      id=body["id"]
      body.pop("id",None)
   #logic
   if mode=="create":
      response=elasticsearch_object.index(index=table,id=id,document=body)
   if mode=="read":
      response=elasticsearch_object.get(index=table,id=id)
   if mode=="update":
      response=elasticsearch_object.update(index=table,id=id,doc=body)
   if mode=="delete":
      response=elasticsearch_object.delete(index=table,id=id)
   if mode=="refresh":
      response=elasticsearch_object.indices.refresh(index=table)
   if mode=="search":
      response=elasticsearch_object.search(index=table,body={"query":{"match":{column:body["keyword"]}},"size":body["size"]})
   #final
   return response
   
#server start
import uvicorn,asyncio
if __name__=="__main__":
   uvicorn_object=uvicorn.Server(config=uvicorn.Config(app,"0.0.0.0",8000,workers=16,log_level="info",reload=False,lifespan="on",loop="asyncio"))
   loop=asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(uvicorn_object.serve())
