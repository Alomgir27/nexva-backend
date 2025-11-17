from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime
import secrets
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255))
    oauth_provider = Column(String(50))
    oauth_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Chatbot(Base):
    __tablename__ = "chatbots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    api_key = Column(String(100), nullable=False, unique=True, index=True, default=lambda: secrets.token_urlsafe(32))
    voice_id = Column(String(50), default="female-1")
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    pages_scraped = Column(Integer, default=0)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScrapedPage(Base):
    __tablename__ = "scraped_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    url = Column(String(1000), nullable=False, index=True)
    title = Column(String(500))
    content = Column(Text)
    content_preview = Column(Text)
    word_count = Column(Integer, default=0)
    media_urls = Column(JSON, default=[])
    media_transcriptions = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    support_requested = Column(Integer, default=0)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=True, index=True)
    mode = Column(String(20), default="ai")
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sender_type = Column(String(20), default="ai")
    sender_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SupportTeamMember(Base):
    __tablename__ = "support_team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="support")
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id"), nullable=False, index=True)
    status = Column(String(20), default="open")
    priority = Column(String(20), default="normal")
    assigned_to = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    pages_scraped = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id"), nullable=False, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, default=0)
    status = Column(String(20), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)

