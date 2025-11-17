from fastapi import APIRouter, WebSocket, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app import database
from app.services import websocket_handler, voice_rtc_service, realtime_voice_service, transcription_service, voice_service, neural_tts_service
from io import BytesIO
from pydub import AudioSegment

router = APIRouter()

@router.websocket("/chat/{api_key}")
async def chat_websocket(websocket: WebSocket, api_key: str):
    db = database.SessionLocal()
    try:
        await websocket_handler.handle_chat_websocket(websocket, api_key, db)
    finally:
        db.close()

@router.websocket("/voice/{api_key}")
async def voice_websocket(websocket: WebSocket, api_key: str):
    await voice_rtc_service.handle_voice_websocket(websocket, api_key)

@router.websocket("/voice-chat/{api_key}")
async def voice_chat_websocket(websocket: WebSocket, api_key: str):
    await realtime_voice_service.handle_voice_chat(websocket, api_key)

@router.websocket("/transcribe/{api_key}")
async def transcription_websocket(websocket: WebSocket, api_key: str):
    await transcription_service.handle_transcription_only(websocket, api_key)

@router.websocket("/support/{ticket_id}")
async def support_websocket(websocket: WebSocket, ticket_id: int, support_email: str):
    db = database.SessionLocal()
    try:
        await websocket_handler.handle_support_websocket(websocket, ticket_id, support_email, db)
    finally:
        db.close()

@router.post("/voice/tts")
async def text_to_speech(text: str):
    audio_data = await voice_service.voice_service.text_to_speech(text)
    return Response(content=audio_data, media_type="audio/wav")

@router.post("/voice/generate-speech")
async def generate_speech(request: dict):
    text = request.get("text", "")
    voice_id = request.get("voice_id", "female-1")
    language = request.get("language", "en")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        audio_data = await neural_tts_service.neural_tts.generate_speech_async(text, voice=voice_id, language=language)
        
        audio = AudioSegment.from_wav(BytesIO(audio_data))
        audio = audio.speedup(playback_speed=1.15)
        
        output = BytesIO()
        audio.export(output, format="wav")
        output.seek(0)
        
        return Response(content=output.read(), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 10,
    before_message_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(database.Message).filter(
        database.Message.conversation_id == conversation_id
    )
    
    if before_message_id:
        query = query.filter(database.Message.id < before_message_id)
    
    messages = query.order_by(database.Message.created_at.desc()).limit(limit).all()
    messages.reverse()
    
    return [{
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "sender_type": msg.sender_type or "ai",
        "sender_email": msg.sender_email,
        "created_at": msg.created_at.isoformat()
    } for msg in messages]

@router.post("/conversations/{conversation_id}/request-support")
async def request_support(
    conversation_id: int,
    db: Session = Depends(database.get_db)
):
    conversation = db.query(database.Conversation).filter(
        database.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.support_requested:
        raise HTTPException(status_code=400, detail="Support already requested")
    
    ticket = database.SupportTicket(
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
    
    support_members = db.query(database.SupportTeamMember).filter(
        database.SupportTeamMember.chatbot_id == conversation.chatbot_id,
        database.SupportTeamMember.status == "active"
    ).all()
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == conversation.chatbot_id
    ).first()
    
    last_message = db.query(database.Message).filter(
        database.Message.conversation_id == conversation_id
    ).order_by(database.Message.created_at.desc()).first()
    
    if support_members and chatbot:
        from app.services import email as email_service
        email_service.send_new_ticket_alert(
            [m.email for m in support_members],
            ticket.id,
            chatbot.name,
            last_message.content if last_message else "New support request"
        )
    
    return {"ticket_id": ticket.id, "message": "Support requested"}

@router.post("/conversations/{conversation_id}/switch-mode")
async def switch_conversation_mode(
    conversation_id: int,
    mode_data: dict,
    db: Session = Depends(database.get_db)
):
    conversation = db.query(database.Conversation).filter(
        database.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    new_mode = mode_data.get("mode", "ai")
    if new_mode not in ["ai", "human"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if new_mode == "human":
        active_ticket = db.query(database.SupportTicket).filter(
            database.SupportTicket.conversation_id == conversation_id,
            database.SupportTicket.status == "pending"
        ).first()
        
        if not active_ticket:
            ticket = database.SupportTicket(
                conversation_id=conversation_id,
                chatbot_id=conversation.chatbot_id
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            conversation.support_requested = 1
            conversation.ticket_id = ticket.id
            
            support_members = db.query(database.SupportTeamMember).filter(
                database.SupportTeamMember.chatbot_id == conversation.chatbot_id,
                database.SupportTeamMember.status == "active"
            ).all()
            
            chatbot = db.query(database.Chatbot).filter(
                database.Chatbot.id == conversation.chatbot_id
            ).first()
            
            if support_members and chatbot:
                last_message = db.query(database.Message).filter(
                    database.Message.conversation_id == conversation_id
                ).order_by(database.Message.created_at.desc()).first()
                
                from app.services import email as email_service
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

