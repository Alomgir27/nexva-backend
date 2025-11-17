from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from app import database, schemas
from app.services import auth
from app.services import email as email_service

router = APIRouter()

@router.post("/chatbots/{chatbot_id}/support-team", response_model=schemas.SupportMemberResponse)
def invite_support_member(
    chatbot_id: int,
    member_data: schemas.SupportMemberInvite,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    existing = db.query(database.SupportTeamMember).filter(
        database.SupportTeamMember.chatbot_id == chatbot_id,
        database.SupportTeamMember.email == member_data.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member already invited")
    
    member = database.SupportTeamMember(
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

@router.get("/chatbots/{chatbot_id}/support-team", response_model=List[schemas.SupportMemberResponse])
def list_support_team(
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
    
    members = db.query(database.SupportTeamMember).filter(
        database.SupportTeamMember.chatbot_id == chatbot_id
    ).all()
    return members

@router.delete("/support-team/{member_id}")
def remove_support_member(
    member_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    member = db.query(database.SupportTeamMember).filter(
        database.SupportTeamMember.id == member_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == member.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(member)
    db.commit()
    return {"message": "Member removed"}

@router.get("/tickets", response_model=List[Dict])
def list_support_tickets(
    chatbot_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(database.SupportTicket).join(database.Chatbot).filter(
        database.Chatbot.user_id == current_user.id
    )
    
    if chatbot_id:
        query = query.filter(database.SupportTicket.chatbot_id == chatbot_id)
    if status:
        query = query.filter(database.SupportTicket.status == status)
    
    tickets = query.order_by(database.SupportTicket.created_at.desc()).all()
    
    result = []
    for ticket in tickets:
        chatbot = db.query(database.Chatbot).filter(database.Chatbot.id == ticket.chatbot_id).first()
        conversation = db.query(database.Conversation).filter(
            database.Conversation.id == ticket.conversation_id
        ).first()
        
        last_message_query = db.query(database.Message).filter(
            database.Message.conversation_id == ticket.conversation_id,
            database.Message.created_at >= ticket.created_at
        )
        
        if ticket.resolved_at:
            last_message_query = last_message_query.filter(
                database.Message.created_at <= ticket.resolved_at
            )
        
        last_message = last_message_query.order_by(database.Message.created_at.desc()).first()
        
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

@router.get("/tickets/{ticket_id}")
def get_support_ticket(
    ticket_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    ticket = db.query(database.SupportTicket).filter(
        database.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == ticket.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    message_query = db.query(database.Message).filter(
        database.Message.conversation_id == ticket.conversation_id,
        database.Message.created_at >= ticket.created_at
    )
    
    if ticket.resolved_at:
        message_query = message_query.filter(
            database.Message.created_at <= ticket.resolved_at
        )
    
    messages = message_query.order_by(database.Message.created_at.asc()).all()
    
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

@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    ticket = db.query(database.SupportTicket).filter(
        database.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == ticket.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    ticket.status = "resolved"
    ticket.resolved_at = datetime.utcnow()
    
    conversation = db.query(database.Conversation).filter(
        database.Conversation.id == ticket.conversation_id
    ).first()
    if conversation:
        conversation.mode = "ai"
    
    db.commit()
    
    from app.services import websocket_handler
    await websocket_handler.manager.send_to_conversation(ticket.conversation_id, {
        'type': 'ticket_resolved',
        'message': 'Your issue has been resolved. Returning to AI assistant.'
    })
    
    return {"message": "Ticket resolved"}

@router.post("/tickets/{ticket_id}/message")
def send_support_message(
    ticket_id: int,
    message_data: dict,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    ticket = db.query(database.SupportTicket).filter(
        database.SupportTicket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == ticket.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    message = database.Message(
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

