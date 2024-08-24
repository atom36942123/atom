#postgres object
from databases import Database
from config import config_postgres_database
postgres_object=Database(config_postgres_database,min_size=1,max_size=100)

