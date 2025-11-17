from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ChatbotCreate(BaseModel):
    name: str
    config: Optional[Dict] = {}

class ChatbotResponse(BaseModel):
    id: int
    name: str
    api_key: str
    config: Dict
    voice_id: Optional[str] = "female-1"
    created_at: datetime

