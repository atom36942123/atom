#postgres object
from databases import Database
config_postgres_object=Database(config_postgres_database_url,min_size=1,max_size=100)

#custom
config_column_datatype=None
