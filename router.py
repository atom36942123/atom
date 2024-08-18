#import
from app import app

#router
from api_root import router as router_root
app.include_router(router_root)

from api_database import router as router_database
app.include_router(router_database)


