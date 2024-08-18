#router
from database import router as router_database
app.include_router(router_database)

from auth import router as router_auth
app.include_router(router_auth)
from my import router as router_my
app.include_router(router_my)

from object import router as router_object
app.include_router(router_object)

from action import router as router_action
app.include_router(router_action)

from message import router as router_message
app.include_router(router_message)

from utility import router as router_utility
app.include_router(router_utility)

from admin import router as router_admin
app.include_router(router_admin)

from feed import router as router_feed
app.include_router(router_feed)

from csvv import router as router_csv
app.include_router(router_csv)

from aws import router as router_aws
app.include_router(router_aws)

from mongo import router as router_mongo
app.include_router(router_mongo)

from elastic import router as router_elasticsearch
app.include_router(router_elasticsearch)
