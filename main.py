import sys
sys.stdout.reconfigure(line_buffering=True)  # Unbuffered logging

from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks, UploadFile, File, Request
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import models
import search
import scraper
import voice_service
import voice_rtc_service
import websocket_handler
import auth_service
import realtime_voice_service
import transcription_service
import email_service
import document_service
import stripe_service
import plan_config
import asyncio
import os
import shutil
import secrets
from r2_service import r2_service

from neural_tts_service import neural_tts

scrape_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="scraper")

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    search.init_elasticsearch()
    print("🚀 Preloading all models...")
    search.get_embedding_model()
    
    from kokoro_service import preload_kokoro
    await preload_kokoro()
    
    print("✅ All models loaded and ready")
    yield
    print("🛑 Shutting down...")
    scrape_executor.shutdown(wait=False)
    await chat_service.chat_service.close()
    print("✅ Cleanup complete")

app = FastAPI(title="Nexva - AI Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    created_at: datetime

class UserUpdate(BaseModel):
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Chatbot Models
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

# Domain Models
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
    model_config = ConfigDict(from_attributes=True)
    id: int
    domain_id: int
    filename: str
    r2_url: str
    file_type: str
    file_size: int
    title: Optional[str]
    content_preview: Optional[str]
    word_count: int
    status: str
    uploaded_at: datetime

class CheckoutSessionCreate(BaseModel):
    plan_tier: str
    billing_period: str = 'monthly'

class SubscriptionInfo(BaseModel):
    plan_tier: str
    status: str
    chatbot_count: int
    chatbot_limit: int
    current_period_end: Optional[datetime]

# Support Models
class SupportMemberInvite(BaseModel):
    email: EmailStr
    name: str

class AcceptInvitationRequest(BaseModel):
    token: str
    password: Optional[str] = None

class SupportMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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

@app.get("/")
def root():
    return {
        "message": "Nexva API",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth/*",
            "chatbots": "/api/chatbots",
            "domains": "/api/domains",
            "websocket": "/ws/chat/{api_key}",
            "widget": "/widget.js"
        }
    }

# Auth Endpoints
@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(models.get_db)):
    user = auth_service.create_user(db, user_data.email, user_data.password)
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(models.get_db)):
    user = auth_service.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth_service.get_current_user)):
    return current_user

@app.put("/api/auth/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    current_user.name = user_data.name
    db.commit()
    db.refresh(current_user)
    return current_user

# Chatbot Endpoints
@app.post("/api/chatbots", response_model=ChatbotResponse)
def create_chatbot(
    chatbot: ChatbotCreate,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    current_count = db.query(models.Chatbot).filter(models.Chatbot.user_id == current_user.id).count()
    
    if not plan_config.can_create_chatbot(current_count, current_user.subscription_tier):
        plan = plan_config.get_plan_limits(current_user.subscription_tier)
        raise HTTPException(
            status_code=403, 
            detail=f"Chatbot limit reached. Your {plan['name']} plan allows {plan['chatbot_limit']} chatbot(s). Please upgrade your plan."
        )
    
    db_chatbot = models.Chatbot(user_id=current_user.id, **chatbot.dict())
    db.add(db_chatbot)
    db.commit()
    db.refresh(db_chatbot)
    
    search.init_chatbot_index(db_chatbot.id)
    
    return db_chatbot

@app.get("/api/chatbots", response_model=List[ChatbotResponse])
def list_chatbots(
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbots = db.query(models.Chatbot).filter(models.Chatbot.user_id == current_user.id).all()
    return chatbots

@app.delete("/api/chatbots/{chatbot_id}")
def delete_chatbot(
    chatbot_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Break circular FK: Set conversation.ticket_id to NULL first
    db.query(models.Conversation).filter(
        models.Conversation.chatbot_id == chatbot_id
    ).update({models.Conversation.ticket_id: None}, synchronize_session=False)
    
    # Delete support tickets
    db.query(models.SupportTicket).filter(models.SupportTicket.chatbot_id == chatbot_id).delete()
    
    # Delete messages for all conversations
    conversations = db.query(models.Conversation).filter(models.Conversation.chatbot_id == chatbot_id).all()
    for conv in conversations:
        db.query(models.Message).filter(models.Message.conversation_id == conv.id).delete()
    
    # Delete conversations
    db.query(models.Conversation).filter(models.Conversation.chatbot_id == chatbot_id).delete()
    
    # Delete support team members
    db.query(models.SupportTeamMember).filter(models.SupportTeamMember.chatbot_id == chatbot_id).delete()
    
    # Delete scraped pages, documents, and jobs for all domains
    domains = db.query(models.Domain).filter(models.Domain.chatbot_id == chatbot_id).all()
    for domain in domains:
        db.query(models.ScrapedPage).filter(models.ScrapedPage.domain_id == domain.id).delete()
        db.query(models.DomainDocument).filter(models.DomainDocument.domain_id == domain.id).delete()
        db.query(models.ScrapeJob).filter(models.ScrapeJob.domain_id == domain.id).delete()
    
    # Delete domains
    db.query(models.Domain).filter(models.Domain.chatbot_id == chatbot_id).delete()
    
    # Delete Elasticsearch index
    try:
        search.es.indices.delete(index=search.get_chatbot_index(chatbot_id), ignore=[404])
    except Exception as e:
        print(f"Warning: Could not delete ES index for chatbot {chatbot_id}: {e}")
    
    # Delete chatbot
    db.delete(chatbot)
    db.commit()
    
    return {"message": "Chatbot deleted successfully"}

@app.put("/api/chatbots/{chatbot_id}/voice")
def update_chatbot_voice(
    chatbot_id: int,
    voice_data: dict,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    chatbot.voice_id = voice_data.get("voice_id", "female-1")
    db.commit()
    db.refresh(chatbot)
    return {"message": "Voice updated successfully", "voice_id": chatbot.voice_id}

@app.get("/api/chatbots/{chatbot_id}/stats")
def get_chatbot_stats(
    chatbot_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    unique_customers = db.query(func.count(func.distinct(models.Conversation.session_id))).filter(
        models.Conversation.chatbot_id == chatbot_id
    ).scalar()
    
    total_conversations = db.query(func.count(models.Conversation.id)).filter(
        models.Conversation.chatbot_id == chatbot_id
    ).scalar()
    
    total_messages = db.query(func.count(models.Message.id)).join(
        models.Conversation
    ).filter(models.Conversation.chatbot_id == chatbot_id).scalar()
    
    return {
        "chatbot_id": chatbot_id,
        "unique_customers": unique_customers or 0,
        "total_conversations": total_conversations or 0,
        "total_messages": total_messages or 0
    }

# Domain Endpoints
@app.post("/api/domains", response_model=DomainResponse)
async def create_domain(
    domain_data: DomainCreate,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain_data.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    domain = models.Domain(chatbot_id=domain_data.chatbot_id, url=domain_data.url, status="scraping")
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    job = models.ScrapeJob(domain_id=domain.id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    scrape_executor.submit(run_domain_scraping, job.id, domain.id, domain_data.url)
    
    return domain

@app.get("/api/domains/{chatbot_id}", response_model=List[DomainResponse])
def list_domains(
    chatbot_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    domains = db.query(models.Domain).filter(models.Domain.chatbot_id == chatbot_id).all()
    return domains

@app.get("/api/domains/{domain_id}/pages", response_model=Dict)
def list_scraped_pages(
    domain_id: int,
    page: int = 1,
    per_page: int = 10,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    offset = (page - 1) * per_page
    pages = db.query(models.ScrapedPage).filter(
        models.ScrapedPage.domain_id == domain_id
    ).offset(offset).limit(per_page).all()
    
    total = db.query(models.ScrapedPage).filter(models.ScrapedPage.domain_id == domain_id).count()
    
    pages_data = [{
        "id": p.id,
        "url": p.url,
        "title": p.title,
        "content": p.content,
        "content_preview": p.content_preview,
        "word_count": p.word_count,
        "tags": p.tags if p.tags else [],
        "last_updated": p.last_updated.isoformat() if p.last_updated else None,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in pages]
    
    return {
        "pages": pages_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.delete("/api/domains/{domain_id}")
def delete_domain(
    domain_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    db.query(models.ScrapedPage).filter(models.ScrapedPage.domain_id == domain_id).delete()
    db.query(models.ScrapeJob).filter(models.ScrapeJob.domain_id == domain_id).delete()
    
    documents = db.query(models.DomainDocument).filter(models.DomainDocument.domain_id == domain_id).all()
    for doc in documents:
        r2_service.delete_file(doc.r2_key)
        document_service.delete_document_from_index(chatbot.id, doc.id)
    db.query(models.DomainDocument).filter(models.DomainDocument.domain_id == domain_id).delete()
    
    db.delete(domain)
    db.commit()
    return {"message": "Domain deleted successfully"}

@app.post("/api/domains/{domain_id}/documents", response_model=DocumentResponse)
async def upload_document(
    domain_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if file.content_type not in allowed_types and not any(file.filename.endswith(ext) for ext in ['.pdf', '.docx', '.txt']):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are allowed")
    
    temp_dir = "/tmp/documents"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(temp_path)
    
    r2_key = r2_service.generate_file_path(domain_id, file.filename)
    content_type = r2_service._get_content_type(file.filename)
    upload_result = r2_service.upload_file(temp_path, r2_key, content_type)
    
    if not upload_result["success"]:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {upload_result.get('error')}")
    
    document = models.DomainDocument(
        domain_id=domain_id,
        filename=file.filename,
        r2_key=r2_key,
        r2_url=upload_result["url"],
        file_type=file.content_type or 'application/octet-stream',
        file_size=file_size,
        status='processing'
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    success = document_service.process_document(document.id, temp_path, file.content_type, chatbot.id, domain_id, db)
    
    os.remove(temp_path)
    
    if not success:
        r2_service.delete_file(r2_key)
        db.delete(document)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to process document")
    
    db.refresh(document)
    return document

@app.get("/api/domains/{domain_id}/documents", response_model=Dict)
def list_documents(
    domain_id: int,
    page: int = 1,
    per_page: int = 10,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    offset = (page - 1) * per_page
    documents = db.query(models.DomainDocument).filter(
        models.DomainDocument.domain_id == domain_id
    ).order_by(models.DomainDocument.uploaded_at.desc()).offset(offset).limit(per_page).all()
    
    total = db.query(models.DomainDocument).filter(models.DomainDocument.domain_id == domain_id).count()
    
    return {
        "documents": [DocumentResponse.model_validate(doc) for doc in documents],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.get("/api/documents/{document_id}/download")
def download_document(
    document_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    document = db.query(models.DomainDocument).filter(models.DomainDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    domain = db.query(models.Domain).filter(models.Domain.id == document.domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=document.r2_url)

@app.delete("/api/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    document = db.query(models.DomainDocument).filter(models.DomainDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    domain = db.query(models.Domain).filter(models.Domain.id == document.domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    r2_service.delete_file(document.r2_key)
    document_service.delete_document_from_index(chatbot.id, document.id)
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

def run_domain_scraping(job_id: int, domain_id: int, start_url: str):
    """
    Background task for domain scraping.
    Runs in background thread - does not block API responses.
    """
    print(f"🚀 Starting scrape: job_id={job_id}, domain_id={domain_id}, url={start_url}")
    db = models.SessionLocal()
    job = None
    domain = None
    
    try:
        job = db.query(models.ScrapeJob).filter(models.ScrapeJob.id == job_id).first()
        domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
        
        if not job or not domain:
            print(f"❌ Job or domain not found: job_id={job_id}, domain_id={domain_id}")
            return
        
        print(f"📊 Starting scraping job for {start_url}")
        job.status = "running"
        domain.status = "scraping"
        db.commit()
        
        print(f"🔧 Initializing WebScraper...")
        enable_media = os.getenv("ENABLE_MEDIA_SCRAPE", "false").lower() == "true"
        web_scraper = scraper.WebScraper(process_media=enable_media)
        
        print(f"🌐 Scraping domain: {start_url}")
        pages = web_scraper.scrape_domain(start_url, domain_id, db)
        
        db.refresh(domain)
        
        job.status = "completed"
        job.pages_scraped = len(pages)
        job.total_pages = len(pages)
        job.completed_at = datetime.utcnow()
        
        domain.status = "completed"
        domain.pages_scraped = len(pages)
        domain.last_scraped_at = datetime.utcnow()
        
        db.commit()
        print(f"✅ Scraping completed: {len(pages)} pages scraped from {start_url}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Scraping error for domain {domain_id}: {e}")
        print(f"❌ Full traceback:\n{error_details}")
        
        try:
            if job:
                job.status = "failed"
                job.error = str(e)
            if domain:
                domain.status = "failed"
            db.commit()
        except Exception as commit_error:
            print(f"❌ Error updating job/domain status: {commit_error}")
            
    finally:
        db.close()

@app.websocket("/ws/chat/{api_key}")
async def chat_websocket(websocket: WebSocket, api_key: str):
    db = models.SessionLocal()
    try:
        await websocket_handler.handle_chat_websocket(websocket, api_key, db)
    finally:
        db.close()

@app.websocket("/ws/voice/{api_key}")
async def voice_websocket(websocket: WebSocket, api_key: str):
    await voice_rtc_service.handle_voice_websocket(websocket, api_key)

@app.websocket("/ws/voice-chat/{api_key}")
async def voice_chat_websocket(websocket: WebSocket, api_key: str):
    """Voice chat with Web Speech API (browser transcription) + LLM + TTS"""
    await realtime_voice_service.handle_voice_chat(websocket, api_key)

@app.websocket("/ws/transcribe/{api_key}")
async def transcription_websocket(websocket: WebSocket, api_key: str):
    """Real-time transcription only (no LLM response)"""
    await transcription_service.handle_transcription_only(websocket, api_key)

@app.websocket("/ws/support/{ticket_id}")
async def support_websocket(websocket: WebSocket, ticket_id: int, token: str):
    """Support team member WebSocket for responding to tickets"""
    db = models.SessionLocal()
    try:
        user = auth_service.get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
        if not ticket:
            await websocket.close(code=4004, reason="Ticket not found")
            return
        
        if not auth_service.verify_support_member_access(user, ticket.chatbot_id, db):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        await websocket_handler.handle_support_websocket(websocket, ticket_id, user, db)
    finally:
        db.close()

@app.post("/api/voice/tts")
async def text_to_speech(text: str):
    audio_data = await voice_service.voice_service.text_to_speech(text)
    return Response(content=audio_data, media_type="audio/wav")

@app.post("/api/voice/generate-speech")
async def generate_speech(request: dict):
    """Generate speech from text using Kokoro-82M"""
    from pydub import AudioSegment
    from io import BytesIO
    
    text = request.get("text", "")
    voice_id = request.get("voice_id", "female-1")
    language = request.get("language", "en")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        audio_data = await neural_tts.generate_speech_async(text, voice=voice_id, language=language)
        
        # Speed up to 1.15x
        audio = AudioSegment.from_wav(BytesIO(audio_data))
        audio = audio.speedup(playback_speed=1.15)
        
        output = BytesIO()
        audio.export(output, format="wav")
        output.seek(0)
        
        return Response(content=output.read(), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

# Support Team Endpoints
@app.post("/api/chatbots/{chatbot_id}/support-team", response_model=SupportMemberResponse)
def invite_support_member(
    chatbot_id: int,
    member_data: SupportMemberInvite,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    existing = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.chatbot_id == chatbot_id,
        models.SupportTeamMember.email == member_data.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member already invited")
    
    invitation_token = secrets.token_urlsafe(32)
    invitation_expires_at = datetime.utcnow() + timedelta(days=7)
    
    member = models.SupportTeamMember(
        chatbot_id=chatbot_id,
        email=member_data.email,
        name=member_data.name,
        invited_by=current_user.id,
        invitation_token=invitation_token,
        invitation_expires_at=invitation_expires_at
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    email_service.send_support_invite(
        member_data.email,
        member_data.name,
        chatbot.name,
        current_user.email,
        invitation_token
    )
    
    return member

@app.post("/api/support/accept-invitation")
def accept_support_invitation(
    request: AcceptInvitationRequest,
    db: Session = Depends(models.get_db)
):
    """Accept support team invitation. Creates account if user doesn't exist."""
    invitation = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.invitation_token == request.token
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    
    if invitation.status == "active":
        raise HTTPException(status_code=400, detail="Invitation already accepted")
    
    if invitation.invitation_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    user = db.query(models.User).filter(models.User.email == invitation.email).first()
    
    if not user:
        if not request.password:
            raise HTTPException(
                status_code=400, 
                detail="Password required for new account"
            )
        
        user = auth_service.create_user(db, invitation.email, request.password)
    
    invitation.status = "active"
    invitation.accepted_at = datetime.utcnow()
    db.commit()
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == invitation.chatbot_id
    ).first()
    
    token = auth_service.create_access_token({"sub": str(user.id)})
    
    return {
        "message": "Invitation accepted successfully",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email
        },
        "chatbot": {
            "id": chatbot.id,
            "name": chatbot.name
        } if chatbot else None
    }

@app.get("/api/support/invitation/{token}")
def get_invitation_details(token: str, db: Session = Depends(models.get_db)):
    """Get invitation details to check if user needs to create account"""
    invitation = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.invitation_token == token
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    
    if invitation.status == "active":
        raise HTTPException(status_code=400, detail="Invitation already accepted")
    
    if invitation.invitation_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == invitation.chatbot_id
    ).first()
    
    user_exists = db.query(models.User).filter(
        models.User.email == invitation.email
    ).first() is not None
    
    return {
        "email": invitation.email,
        "name": invitation.name,
        "chatbot_name": chatbot.name if chatbot else "Unknown",
        "user_exists": user_exists,
        "expires_at": invitation.invitation_expires_at.isoformat()
    }

@app.get("/api/chatbots/{chatbot_id}/support-team", response_model=List[SupportMemberResponse])
def list_support_team(
    chatbot_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    members = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.chatbot_id == chatbot_id
    ).all()
    return members

@app.delete("/api/support-team/{member_id}")
def remove_support_member(
    member_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    member = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.id == member_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == member.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(member)
    db.commit()
    return {"message": "Member removed"}

# Support Ticket Endpoints
@app.get("/api/support/tickets", response_model=List[Dict])
def list_support_tickets(
    chatbot_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    accessible_chatbot_ids = auth_service.get_accessible_chatbot_ids(current_user, db)
    
    if not accessible_chatbot_ids:
        return []
    
    query = db.query(models.SupportTicket).filter(
        models.SupportTicket.chatbot_id.in_(accessible_chatbot_ids)
    )
    
    if chatbot_id:
        if chatbot_id not in accessible_chatbot_ids:
            raise HTTPException(status_code=403, detail="Access denied to this chatbot")
        query = query.filter(models.SupportTicket.chatbot_id == chatbot_id)
    
    if status:
        query = query.filter(models.SupportTicket.status == status)
    
    tickets = query.order_by(models.SupportTicket.created_at.desc()).all()
    
    result = []
    for ticket in tickets:
        chatbot = db.query(models.Chatbot).filter(models.Chatbot.id == ticket.chatbot_id).first()
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == ticket.conversation_id
        ).first()
        
        last_message_query = db.query(models.Message).filter(
            models.Message.conversation_id == ticket.conversation_id,
            models.Message.created_at >= ticket.created_at
        )
        
        if ticket.resolved_at:
            last_message_query = last_message_query.filter(
                models.Message.created_at <= ticket.resolved_at
            )
        
        last_message = last_message_query.order_by(models.Message.created_at.desc()).first()
        
        result.append({
            "id": ticket.id,
            "conversation_id": ticket.conversation_id,
            "chatbot_id": ticket.chatbot_id,
            "chatbot_name": chatbot.name if chatbot else "Unknown",
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_to": ticket.assigned_to,
            "last_message": last_message.content if last_message else "",
            "created_at": ticket.created_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
        })
    
    return result

@app.get("/api/support/tickets/{ticket_id}")
def get_support_ticket(
    ticket_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    ticket = db.query(models.SupportTicket).filter(
        models.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not auth_service.verify_support_member_access(current_user, ticket.chatbot_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    message_query = db.query(models.Message).filter(
        models.Message.conversation_id == ticket.conversation_id,
        models.Message.created_at >= ticket.created_at
    )
    
    if ticket.resolved_at:
        message_query = message_query.filter(
            models.Message.created_at <= ticket.resolved_at
        )
    
    messages = message_query.order_by(models.Message.created_at.asc()).all()
    
    return {
        "ticket": {
            "id": ticket.id,
            "conversation_id": ticket.conversation_id,
            "chatbot_id": ticket.chatbot_id,
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_to": ticket.assigned_to,
            "created_at": ticket.created_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
        },
        "messages": [{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sender_type": msg.sender_type,
            "sender_email": msg.sender_email,
            "created_at": msg.created_at.isoformat()
        } for msg in messages]
    }

@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 10,
    before_message_id: Optional[int] = None,
    db: Session = Depends(models.get_db)
):
    query = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    )
    
    if before_message_id:
        query = query.filter(models.Message.id < before_message_id)
    
    messages = query.order_by(models.Message.created_at.desc()).limit(limit).all()
    messages.reverse()
    
    return [{
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "sender_type": msg.sender_type or "ai",
        "sender_email": msg.sender_email,
        "created_at": msg.created_at.isoformat()
    } for msg in messages]

@app.post("/api/conversations/{conversation_id}/request-support")
async def request_support(
    conversation_id: int,
    db: Session = Depends(models.get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.support_requested:
        raise HTTPException(status_code=400, detail="Support already requested")
    
    ticket = models.SupportTicket(
        conversation_id=conversation_id,
        chatbot_id=conversation.chatbot_id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    conversation.support_requested = 1
    conversation.ticket_id = ticket.id
    conversation.mode = "human"
    db.commit()
    
    support_members = db.query(models.SupportTeamMember).filter(
        models.SupportTeamMember.chatbot_id == conversation.chatbot_id,
        models.SupportTeamMember.status == "active"
    ).all()
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == conversation.chatbot_id
    ).first()
    
    last_message = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.desc()).first()
    
    if support_members and chatbot:
        email_service.send_new_ticket_alert(
            [m.email for m in support_members],
            ticket.id,
            chatbot.name,
            last_message.content if last_message else "New support request"
        )
    
    return {"ticket_id": ticket.id, "message": "Support requested"}

@app.post("/api/conversations/{conversation_id}/switch-mode")
async def switch_conversation_mode(
    conversation_id: int,
    mode_data: dict,
    db: Session = Depends(models.get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    new_mode = mode_data.get("mode", "ai")
    if new_mode not in ["ai", "human"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if new_mode == "human":
        # Check for existing open or in_progress ticket for this conversation
        active_ticket = db.query(models.SupportTicket).filter(
            models.SupportTicket.conversation_id == conversation_id,
            models.SupportTicket.status.in_(["open", "in_progress"])
        ).first()
        
        if not active_ticket:
            # No active ticket exists, create a new one
            ticket = models.SupportTicket(
                conversation_id=conversation_id,
                chatbot_id=conversation.chatbot_id
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            conversation.support_requested = 1
            conversation.ticket_id = ticket.id
            
            support_members = db.query(models.SupportTeamMember).filter(
                models.SupportTeamMember.chatbot_id == conversation.chatbot_id,
                models.SupportTeamMember.status == "active"
            ).all()
            
            chatbot = db.query(models.Chatbot).filter(
                models.Chatbot.id == conversation.chatbot_id
            ).first()
            
            if support_members and chatbot:
                last_message = db.query(models.Message).filter(
                    models.Message.conversation_id == conversation_id
                ).order_by(models.Message.created_at.desc()).first()
                
                email_service.send_new_ticket_alert(
                    [m.email for m in support_members],
                    ticket.id,
                    chatbot.name,
                    last_message.content if last_message else "New support request"
                )
        else:
            # Reuse existing active ticket
            conversation.ticket_id = active_ticket.id
    
    conversation.mode = new_mode
    db.commit()
    
    return {"mode": new_mode, "message": f"Switched to {new_mode} mode"}

@app.post("/api/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    ticket = db.query(models.SupportTicket).filter(
        models.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not auth_service.verify_support_member_access(current_user, ticket.chatbot_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    ticket.status = "resolved"
    ticket.resolved_at = datetime.utcnow()
    
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == ticket.conversation_id
    ).first()
    if conversation:
        conversation.mode = "ai"
    
    db.commit()
    
    import websocket_handler
    await websocket_handler.manager.send_to_conversation(ticket.conversation_id, {
        'type': 'ticket_resolved',
        'message': 'Your issue has been resolved. Returning to AI assistant.'
    })
    
    return {"message": "Ticket resolved"}

@app.post("/api/support/tickets/{ticket_id}/message")
def send_support_message(
    ticket_id: int,
    message_data: dict,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    ticket = db.query(models.SupportTicket).filter(
        models.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not auth_service.verify_support_member_access(current_user, ticket.chatbot_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    message = models.Message(
        conversation_id=ticket.conversation_id,
        role='assistant',
        content=message_data.get('message', ''),
        sender_type='support',
        sender_email=current_user.email
    )
    db.add(message)
    
    if ticket.status == "open":
        ticket.status = "in_progress"
        ticket.assigned_to = current_user.email
    
    db.commit()
    db.refresh(message)
    
    return {"message": "Message sent", "id": message.id}

# Billing Endpoints
@app.post("/api/billing/create-checkout-session")
async def create_checkout_session(
    session_data: CheckoutSessionCreate,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    if session_data.plan_tier not in ['basic', 'pro', 'enterprise']:
        raise HTTPException(status_code=400, detail="Invalid plan tier")
    
    if session_data.billing_period not in ['monthly', 'annual']:
        raise HTTPException(status_code=400, detail="Invalid billing period")
    
    success_url = os.getenv('FRONTEND_URL', 'https://nexva.pages.dev') + '/dashboard/billing?success=true'
    cancel_url = os.getenv('FRONTEND_URL', 'https://nexva.pages.dev') + '/dashboard/billing?canceled=true'
    
    result = stripe_service.create_checkout_session(
        current_user, session_data.plan_tier, session_data.billing_period, success_url, cancel_url, db
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    
    return result

@app.get("/api/billing/portal-session")
async def create_portal_session(
    current_user: models.User = Depends(auth_service.get_current_user)
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing account found")
    
    return_url = os.getenv('FRONTEND_URL', 'https://nexva.pages.dev') + '/dashboard/billing'
    
    portal_url = stripe_service.create_portal_session(current_user.stripe_customer_id, return_url)
    
    if not portal_url:
        raise HTTPException(status_code=500, detail="Failed to create portal session")
    
    return {"url": portal_url}

@app.get("/api/billing/subscription", response_model=SubscriptionInfo)
async def get_subscription(
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot_count = db.query(models.Chatbot).filter(models.Chatbot.user_id == current_user.id).count()
    plan = plan_config.get_plan_limits(current_user.subscription_tier)
    
    subscription = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id,
        models.Subscription.status.in_(['active', 'trialing'])
    ).first()
    
    return {
        "plan_tier": current_user.subscription_tier,
        "status": subscription.status if subscription else "inactive",
        "chatbot_count": chatbot_count,
        "chatbot_limit": plan['chatbot_limit'],
        "current_period_end": subscription.current_period_end if subscription else None
    }

@app.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(models.get_db)
):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    success = stripe_service.handle_webhook(payload, sig_header, db)
    
    if not success:
        raise HTTPException(status_code=400, detail="Webhook handling failed")
    
    return {"status": "success"}

@app.get("/widget.js")
async def serve_widget():
    import os
    widget_path = os.path.join(os.path.dirname(__file__), "widget", "widget.js")
    return FileResponse(
        widget_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/notifications.wav")
async def serve_notification_sound():
    """Serve notification sound"""
    import os
    audio_path = os.path.join(os.path.dirname(__file__), "notifications.wav")
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        }
    )

@app.get("/intro.wav")
async def serve_intro_sound():
    """Serve intro sound for voice chat"""
    import os
    audio_path = os.path.join(os.path.dirname(__file__), "intro.wav")
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        }
    )


@app.get("/src/{filename:path}")
async def serve_widget_src(filename: str):
    """Serve widget source modules"""
    import os
    src_path = os.path.join(os.path.dirname(__file__), "widget", "src", filename)
    
    # Security check - prevent directory traversal
    widget_src_dir = os.path.join(os.path.dirname(__file__), "widget", "src")
    if not os.path.abspath(src_path).startswith(os.path.abspath(widget_src_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(src_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        src_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "X-Content-Type-Options": "nosniff"
        }
    )

