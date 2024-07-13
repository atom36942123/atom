#app
from fastapi import FastAPI
from lifespan import lifespan
app=FastAPI(lifespan=lifespan)

#cors
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

#import
from middleware import *

#api
@app.get("/")
async def api_func_root():
   return {"status":1,"message":"welcome to atom"}

@app.get("/{x}")
async def api_func_root(x:str):
   return {"status":1,"message":f"welcome to {x}"}

#router
from api_database import router
app.include_router(router)
from api_login import router
app.include_router(router)
from api_my import router
app.include_router(router)
from api_crud import router
app.include_router(router)
from api_utility import router
app.include_router(router)
from api_admin import router
app.include_router(router)
from api_zzz import router
app.include_router(router)
