#import
from app import app

#router
from root import router as router_root
app.include_router(router_root)

