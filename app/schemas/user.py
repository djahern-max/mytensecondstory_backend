from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import OAuthProvider

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: Optional[str] = None
    oauth_provider: Optional[OAuthProvider] = None
    oauth_id: Optional[str] = None

# Properties to receive via OAuth
class UserOAuthCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    oauth_provider: OAuthProvider
    oauth_id: str
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None

# Properties to return via API
class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Properties for authentication
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None