#app
from fastapi import FastAPI
from lifespan import function_lifespan
app=FastAPI(lifespan=function_lifespan,title="atom")
