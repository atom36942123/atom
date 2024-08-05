#env read
from environs import Env
env=Env()
env.read_env()

#postgres object
from databases import Database
postgres_object={item.split("/")[-1]:Database(item,min_size=1,max_size=100) for item in env("postgres_url").split(",")}


