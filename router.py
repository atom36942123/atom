#import
from app import app

#auth
from api_01_auth import router as router_auth
app.include_router(router_auth)

#my
from api_02_my import router as router_my
app.include_router(router_my)

#object
from api_03_object import router as router_object
app.include_router(router_object)

#action
from api_04_action import router as router_action
app.include_router(router_action)

#message
from api_05_message import router as router_message
app.include_router(router_message)

#utility
from api_06_utility import router as router_utility
app.include_router(router_utility)

#admin
from api_07_admin import router as router_admin
app.include_router(router_admin)

#database
from api_08_database import router as router_database
app.include_router(router_database)

#csv
from api_09_csv import router as router_csv
app.include_router(router_csv)

#aws
from api_10_aws import router as router_aws
app.include_router(router_aws)

#mongo
from api_11_mongo import router as router_mongo
app.include_router(router_mongo)

#elasticsearch
from api_12_elasticsearch import router as router_elasticsearch
app.include_router(router_elasticsearch)
