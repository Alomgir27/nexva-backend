from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app import database

router = APIRouter()

@router.get("/{conversation_id}/messages")
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

@router.post("/{conversation_id}/request-support")
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

@router.post("/{conversation_id}/switch-mode")
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

