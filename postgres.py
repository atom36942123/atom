#import
from config import config_postgres_database_uri
from databases import Database

#logic
postgres_object_dict={}
postgres_url_list=config_postgres_database_uri.split(",")
for item in postgres_url_list:
  postgres_object=Database(item,min_size=1,max_size=100)
  database_name=item.split("/")[-1]
  postgres_object_dict={database_name:postgres_object}

