from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SupportMemberInvite(BaseModel):
    email: EmailStr
    name: str

class SupportMemberResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    status: str
    created_at: datetime

class TicketResponse(BaseModel):
    id: int
    conversation_id: int
    chatbot_id: int
    status: str
    priority: str
    created_at: datetime
    resolved_at: Optional[datetime]

