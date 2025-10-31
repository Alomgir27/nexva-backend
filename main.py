from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from datetime import datetime
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
import asyncio

from neural_tts_service import neural_tts

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    search.init_elasticsearch()
    yield

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
    created_at: datetime

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

# Support Models
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

# Chatbot Endpoints
@app.post("/api/chatbots", response_model=ChatbotResponse)
def create_chatbot(
    chatbot: ChatbotCreate,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
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

# Domain Endpoints
@app.post("/api/domains", response_model=DomainResponse)
async def create_domain(
    domain_data: DomainCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(auth_service.get_current_user),
    db: Session = Depends(models.get_db)
):
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == domain_data.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Create domain immediately
    domain = models.Domain(chatbot_id=domain_data.chatbot_id, url=domain_data.url, status="scraping")
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    # Create scrape job
    job = models.ScrapeJob(domain_id=domain.id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Add to background tasks - this returns immediately!
    background_tasks.add_task(run_domain_scraping, job.id, domain.id, domain_data.url)
    
    # Return immediately - scraping continues in background
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
    
    db.delete(domain)
    db.commit()
    return {"message": "Domain deleted successfully"}

def run_domain_scraping(job_id: int, domain_id: int, start_url: str):
    """
    Background task for domain scraping.
    Runs in background thread - does not block API responses.
    """
    db = models.SessionLocal()
    try:
        job = db.query(models.ScrapeJob).filter(models.ScrapeJob.id == job_id).first()
        domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
        
        if not job or not domain:
            print(f"Job or domain not found: job_id={job_id}, domain_id={domain_id}")
            return
        
        job.status = "running"
        domain.status = "scraping"
        db.commit()
        
        web_scraper = scraper.WebScraper()
        pages = web_scraper.scrape_domain(start_url, domain_id, db)
        
        # Refresh domain object to get latest state
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
        print(f"Scraping error for domain {domain_id}: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
        if domain:
            domain.status = "failed"
        db.commit()
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
async def support_websocket(websocket: WebSocket, ticket_id: int, support_email: str):
    """Support team member WebSocket for responding to tickets"""
    db = models.SessionLocal()
    try:
        await websocket_handler.handle_support_websocket(websocket, ticket_id, support_email, db)
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
    
    member = models.SupportTeamMember(
        chatbot_id=chatbot_id,
        email=member_data.email,
        name=member_data.name,
        invited_by=current_user.id
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    email_service.send_support_invite(
        member_data.email,
        member_data.name,
        chatbot.name,
        current_user.email
    )
    
    return member

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
    query = db.query(models.SupportTicket).join(models.Chatbot).filter(
        models.Chatbot.user_id == current_user.id
    )
    
    if chatbot_id:
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
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == ticket.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
        active_ticket = db.query(models.SupportTicket).filter(
            models.SupportTicket.conversation_id == conversation_id,
            models.SupportTicket.status == "pending"
        ).first()
        
        if not active_ticket:
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
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == ticket.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    
    chatbot = db.query(models.Chatbot).filter(
        models.Chatbot.id == ticket.chatbot_id,
        models.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    message = models.Message(
        conversation_id=ticket.conversation_id,
        role='assistant',
        content=message_data.get('message', ''),
        sender_type='support',
        sender_email=message_data.get('sender_email', current_user.email)
    )
    db.add(message)
    
    if ticket.status == "open":
        ticket.status = "in_progress"
    
    db.commit()
    db.refresh(message)
    
    return {"message": "Message sent", "id": message.id}

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

