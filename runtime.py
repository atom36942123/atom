#postgres object
from config import config_postgres_database_url
from databases import Database
postgres_object=Database(config_postgres_database_url,min_size=1,max_size=100)

#column datatype
from function import function_postgres_column_datatype
response=function_postgres_column_datatype(postgres_object)
config_column_datatype=response["message"]


