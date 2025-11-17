from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DomainCreate(BaseModel):
    chatbot_id: int
    url: str

class DomainResponse(BaseModel):
    id: int
    chatbot_id: int
    url: str
    status: str
    pages_scraped: int
    last_scraped_at: Optional[datetime]
    created_at: datetime

class ScrapedPageResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    content_preview: Optional[str]
    word_count: int
    tags: Optional[List[str]] = []
    last_updated: datetime

class DocumentResponse(BaseModel):
    id: int
    chatbot_id: int
    domain_id: int
    file_name: str
    mime_type: Optional[str]
    file_size: int
    status: str
    created_at: datetime

