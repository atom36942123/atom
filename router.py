#import
from app import app

#router
from database import router as router_database
app.include_router(router_database)

