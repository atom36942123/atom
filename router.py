#import
from app import app

#auth
from api_auth import router as router_auth
app.include_router(router_auth)

#my
from api_my import router as router_my
app.include_router(router_my)

#object
from api_object import router as router_object
app.include_router(router_object)

#action
from api_action import router as router_action
app.include_router(router_action)

#message
from api_message import router as router_message
app.include_router(router_message)

#utility
from api_utility import router as router_utility
app.include_router(router_utility)

#admin
from api_admin import router as router_admin
app.include_router(router_admin)

#database
from api_database import router as router_database
app.include_router(router_database)

#csv
from api_csv import router as router_csv
app.include_router(router_csv)


