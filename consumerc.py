#function
from function import function_postgres_object_create_asyncpg

#env
import os
from dotenv import load_dotenv
load_dotenv()

#config
config_redis_url=os.getenv("config_redis_url")
config_postgres_url=os.getenv("config_postgres_url")

#import
import asyncio,traceback,asyncpg
from celery import Celery,signals

#client
client_celery_consumer=Celery("worker",broker=config_redis_url,backend=config_redis_url)
client_postgres_asyncpg_pool=None

#startup
@signals.worker_process_init.connect
def init_worker(**kwargs):
    global client_postgres_asyncpg_pool
    loop=asyncio.get_event_loop()
    client_postgres_asyncpg_pool=loop.run_until_complete(asyncpg.create_pool(dsn=config_postgres_url,min_size=1,max_size=100))
    print("✅ asyncpg pool created")

#shutdown
@signals.worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global client_postgres_asyncpg_pool
    loop=asyncio.get_event_loop()
    loop.run_until_complete(client_postgres_asyncpg_pool.close())
    print("🛑 asyncpg pool closed")

#task 1
@client_celery_consumer.task(name="tasks.celery_task_postgres_object_create")
def celery_task_postgres_object_create(table,object_list):
    try:
        def run_wrapper():
            async def wrapper():
                global client_postgres_asyncpg_pool
                async with client_postgres_asyncpg_pool.acquire() as client_postgres_asyncpg:
                    await function_postgres_object_create_asyncpg(table,object_list,client_postgres_asyncpg)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(wrapper())
        return run_wrapper()
    except Exception as e:
        print("Exception occurred:",str(e))
        traceback.print_exc()
        return None

#task 2
@client_celery_consumer.task(name="tasks.celery_add_num")
def celery_add_num(x,y):
   print(x+y)
   return None