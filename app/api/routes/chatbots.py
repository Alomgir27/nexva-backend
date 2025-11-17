from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app import database, schemas
from app.services import auth, search

router = APIRouter()

@router.post("", response_model=schemas.ChatbotResponse)
def create_chatbot(
    chatbot: schemas.ChatbotCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_chatbot = database.Chatbot(user_id=current_user.id, **chatbot.dict())
    db.add(db_chatbot)
    db.commit()
    db.refresh(db_chatbot)
    
    search.init_chatbot_index(db_chatbot.id)
    return db_chatbot

@router.get("", response_model=List[schemas.ChatbotResponse])
def list_chatbots(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbots = db.query(database.Chatbot).filter(database.Chatbot.user_id == current_user.id).all()
    return chatbots

@router.delete("/{chatbot_id}")
def delete_chatbot(
    chatbot_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    db.delete(chatbot)
    db.commit()
    return {"message": "Chatbot deleted successfully"}

@router.get("/{chatbot_id}/stats")
def get_chatbot_stats(
    chatbot_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    total_conversations = db.query(database.Conversation).filter(
        database.Conversation.chatbot_id == chatbot_id
    ).count()
    
    unique_customers = db.query(func.count(func.distinct(database.Conversation.session_id))).filter(
        database.Conversation.chatbot_id == chatbot_id,
        database.Conversation.session_id.isnot(None)
    ).scalar() or 0
    
    total_messages = db.query(database.Message).join(database.Conversation).filter(
        database.Conversation.chatbot_id == chatbot_id
    ).count()
    
    return {
        "total_conversations": total_conversations,
        "unique_customers": unique_customers,
        "total_messages": total_messages
    }

@router.put("/{chatbot_id}/voice")
def update_chatbot_voice(
    chatbot_id: int,
    voice_data: dict,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    chatbot.voice_id = voice_data.get("voice_id", "female-1")
    db.commit()
    db.refresh(chatbot)
    return {"message": "Voice updated successfully", "voice_id": chatbot.voice_id}

