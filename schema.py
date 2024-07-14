#import
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

#signup
class schema_signup(BaseModel):
    username:str
    password:str
   
   

#login
class schema_login(BaseModel):
    mode:Literal["username","firebase","email","mobile"]="username"
    username:str|None=None
    password:str|None=None
    firebase_id:str|None=None
    email:str|None=None
    mobile:str|None=None
    otp:int|None=None
   
   
   
   
   
   
   

#atom

