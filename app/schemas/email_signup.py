from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmailSignupBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class EmailSignupCreate(EmailSignupBase):
    pass

class EmailSignup(EmailSignupBase):
    id: str
    is_notified: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class EmailSignupStats(BaseModel):
    total_signups: int
    recent_signups: int  # Last 24 hours
