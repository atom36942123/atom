#import
from app import app

#database
from api_database import router as router_database
app.include_router(router_database)

#auth
from api_auth import router as router_auth
app.include_router(router_auth)


