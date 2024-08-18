#import
from app import app

#router
from api_root import router as router_root
app.include_router(router_root)

