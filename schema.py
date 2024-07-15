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
class schema_atom(BaseModel):
    id:int|None=None
    created_at:datetime|None=None
    created_by_id:int|None=None
    updated_at:datetime|None=None
    updated_by_id:int|None=None
    is_active:int|None=None
    is_verified:int|None=None
    parent_table:str|None=None
    parent_id:int|None=None
    received_by_id:int|None=None
    last_active_at:datetime|None=None
    firebase_id:str|None=None
    otp:int|None=None
    metadata:dict|None=None

    username:str|None=None
    password:str|None=None
    profile_pic_url:str|None=None
    date_of_birth:datetime|None=None
    name:str|None=None
    gender:str|None=None
    email:str|None=None
    mobile:str|None=None
    whatsapp:str|None=None
    phone:str|None=None
    country:str|None=None
    state:str|None=None
    city:str|None=None

    type:str|None=None
    title:str|None=None
    description:str|None=None
    file_url:str|None=None
    link_url:str|None=None
    tag:list|None=None
    number:float|None=None
    date:datetime|None=None
    status:str|None=None
    remark:str|None=None
    rating:int|None=None
    is_pinned:int|None=None

    work_type:str|None=None
    work_profile:str|None=None
    degree:str|None=None
    college:str|None=None
    linkedin_url:str|None=None
    portfolio_url:str|None=None
    experience:int|None=None
    experience_work_profile:int|None=None
    is_working:int|None=None
    location_current:str|None=None
    location_expected:str|None=None
    currency:str|None=None
    salary_frequency:str|None=None
    salary_current:int|None=None
    salary_expected:int|None=None
    sector:str|None=None
    past_company_count:int|None=None
    past_company_name:str|None=None
    marital_status:str|None=None
    physical_disability:str|None=None
    hobby:str|None=None
    language:str|None=None
    joining_days:int|None=None
    career_break_month:int|None=None
    resume_url:str|None=None
    achievement:str|None=None
    certificate:str|None=None
    project:str|None=None
    is_founder:int|None=None


