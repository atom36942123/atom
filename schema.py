#import
from pydantic import BaseModel
from typing import Literal

#schema
class schema_signup(BaseModel):
   username:str
   password:str
   
class schema_login(BaseModel):
   mode:Literal["username","firebase","email","mobile"]="username"
   username:str|None=None
   password:str|None=None
   firebase_id:str|None=None
   email:str|None=None
   mobile:str|None=None
   otp:int|None=None
