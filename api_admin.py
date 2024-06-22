#import
from config import *
from function import *
from object import postgres_object
from fastapi import Request
from fastapi import BackgroundTasks
from datetime import datetime
from typing import Literal
import json
import random
from fastapi import File
from fastapi import UploadFile
from fastapi import Body
import csv,codecs
from fastapi_cache.decorator import cache

#router
from fastapi import APIRouter
router=APIRouter(tags=["admin"])
