#app
from fastapi import FastAPI
from lifesoan import lifespan
app=FastAPI(lifespan=lifespan,title="atom")
