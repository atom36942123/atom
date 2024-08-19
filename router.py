#import
from app import app

#database
from api_database import router as router_database
app.include_router(router_database)

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


