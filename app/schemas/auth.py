from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

