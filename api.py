#router
from fastapi import APIRouter
router=APIRouter()

#import
from function import *
from fastapi import Request,BackgroundTasks,Depends,Body,File,UploadFile
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter
import hashlib,json,random,csv,codecs
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from elasticsearch import Elasticsearch
import boto3,uuid
