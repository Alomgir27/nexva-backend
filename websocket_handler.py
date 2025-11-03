from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import models
import chat_service
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.support_connections: dict = {}
        self.conversation_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, conversation_id: int = None):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if conversation_id:
            self.conversation_connections[conversation_id] = websocket
    
    def disconnect(self, session_id: str, conversation_id: int = None):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if conversation_id and conversation_id in self.conversation_connections:
            del self.conversation_connections[conversation_id]
    
    async def send_message(self, session_id: str, message: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)
    
    async def send_to_conversation(self, conversation_id: int, message: dict):
        if conversation_id in self.conversation_connections:
            try:
                await self.conversation_connections[conversation_id].send_json(message)
                return True
            except Exception as e:
                del self.conversation_connections[conversation_id]
                return False
        return False
    
    async def connect_support(self, websocket: WebSocket, ticket_id: int):
        await websocket.accept()
        if ticket_id not in self.support_connections:
            self.support_connections[ticket_id] = []
        self.support_connections[ticket_id].append(websocket)
    
    def disconnect_support(self, websocket: WebSocket, ticket_id: int):
        if ticket_id in self.support_connections:
            if websocket in self.support_connections[ticket_id]:
                self.support_connections[ticket_id].remove(websocket)
    
    async def broadcast_to_ticket(self, ticket_id: int, message: dict):
        if ticket_id in self.support_connections:
            for ws in self.support_connections[ticket_id]:
                try:
                    await ws.send_json(message)
                except:
                    pass

manager = ConnectionManager()

async def handle_chat_websocket(websocket: WebSocket, api_key: str, db: Session):
    chatbot = db.query(models.Chatbot).filter(models.Chatbot.api_key == api_key).first()
    
    if not chatbot:
        await websocket.close(code=4001, reason="Invalid API key")
        return
    
    await websocket.accept()
    ws_id = id(websocket)
    
    conversation_id = None
    session_id = None
    conversation = None
    
    try:
        data = await websocket.receive_text()
        init_data = json.loads(data)
        
        session_id = init_data.get('session_id', f"{api_key}_{datetime.utcnow().timestamp()}")
        conversation_id = init_data.get('conversation_id')
    except Exception as e:
        session_id = f"{api_key}_{datetime.utcnow().timestamp()}"
    
    history = []
    
    if conversation_id:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id,
            models.Conversation.chatbot_id == chatbot.id
        ).first()
        
        if conversation:
            if conversation.id in manager.conversation_connections:
                old_ws = manager.conversation_connections[conversation.id]
                if old_ws != websocket:
                    try:
                        await old_ws.close(code=1000, reason="Reconnected from another session")
                    except:
                        pass
            manager.conversation_connections[conversation.id] = websocket
            
            if conversation.ticket_id:
                ticket = db.query(models.SupportTicket).filter(
                    models.SupportTicket.id == conversation.ticket_id
                ).first()
                if ticket and ticket.conversation_id != conversation.id:
                    ticket.conversation_id = conversation.id
                    db.commit()
            
            messages = db.query(models.Message).filter(
                models.Message.conversation_id == conversation_id
            ).order_by(models.Message.created_at.desc()).limit(10).all()
            messages.reverse()
            
            await websocket.send_json({
                'type': 'history',
                'messages': [{
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'sender_type': msg.sender_type or 'ai',
                    'sender_email': msg.sender_email,
                    'created_at': msg.created_at.isoformat()
                } for msg in messages],
                'mode': conversation.mode or 'ai'
            })
            
            history = [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    if not conversation:
        conversation = models.Conversation(
            chatbot_id=chatbot.id,
            session_id=session_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        manager.conversation_connections[conversation.id] = websocket
        
        await websocket.send_json({
            'type': 'complete',
            'conversation_id': conversation.id
        })
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get('type') == 'ping':
                continue
            
            user_message = message_data.get('message', '')
            
            if not user_message or not user_message.strip():
                continue
            
            db_message = models.Message(
                conversation_id=conversation.id,
                role='user',
                content=user_message
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            db.refresh(conversation)
            
            if conversation.mode == "human":
                if conversation.ticket_id:
                    await manager.broadcast_to_ticket(conversation.ticket_id, {
                        'type': 'message',
                        'message': {
                            'id': db_message.id,
                            'role': 'user',
                            'content': user_message,
                            'sender_type': 'user',
                            'created_at': db_message.created_at.isoformat()
                        }
                    })
                continue
            
            history.append({'role': 'user', 'content': user_message})
            
            if len(history) > 20:
                history = history[-20:]
            
            full_response = ""
            async for chunk in chat_service.chat_service.stream_chat(chatbot.id, user_message, history):
                full_response += chunk
                await websocket.send_json({
                    'type': 'chunk',
                    'text': chunk
                })
            
            await websocket.send_json({
                'type': 'complete',
                'response': full_response,
                'conversation_id': conversation.id
            })
            
            history.append({'role': 'assistant', 'content': full_response})
            
            if len(history) > 20:
                history = history[-20:]
            
            db_response = models.Message(
                conversation_id=conversation.id,
                role='assistant',
                content=full_response
            )
            db.add(db_response)
            db.commit()
    
    except WebSocketDisconnect:
        if conversation and conversation.id in manager.conversation_connections:
            if manager.conversation_connections[conversation.id] == websocket:
                del manager.conversation_connections[conversation.id]
    except Exception as e:
        import traceback
        traceback.print_exc()
        if conversation and conversation.id in manager.conversation_connections:
            if manager.conversation_connections[conversation.id] == websocket:
                del manager.conversation_connections[conversation.id]

async def handle_support_websocket(websocket: WebSocket, ticket_id: int, user: models.User, db: Session):
    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
    
    if not ticket:
        await websocket.close(code=4001, reason="Invalid ticket")
        return
    
    await manager.connect_support(websocket, ticket_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            content = message_data.get('message', '')
            
            if not content.strip():
                continue
            
            db.refresh(ticket)
            
            if ticket.status == "resolved":
                await websocket.send_json({
                    'type': 'error',
                    'message': 'This ticket has been resolved. Please reopen it to continue.'
                })
                continue
            
            db_message = models.Message(
                conversation_id=ticket.conversation_id,
                role='assistant',
                content=content,
                sender_type='support',
                sender_email=user.email
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            if ticket.status == "open":
                ticket.status = "in_progress"
                ticket.assigned_to = user.email
                db.commit()
            
            message_obj = {
                'id': db_message.id,
                'role': 'assistant',
                'content': content,
                'sender_type': 'support',
                'sender_email': user.email,
                'created_at': db_message.created_at.isoformat()
            }
            
            await manager.broadcast_to_ticket(ticket_id, {
                'type': 'message',
                'message': message_obj
            })
            
            await manager.send_to_conversation(ticket.conversation_id, {
                'type': 'human_message',
                'content': content,
                'sender_email': user.email,
                'timestamp': db_message.created_at.isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect_support(websocket, ticket_id)
    except Exception as e:
        manager.disconnect_support(websocket, ticket_id)

