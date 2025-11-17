from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
from app import database
from app.services.chat import chat_service
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
        print(f"[WebSocket] Attempting to send to conversation {conversation_id}")
        print(f"[WebSocket] Active connections: {list(self.conversation_connections.keys())}")
        if conversation_id in self.conversation_connections:
            try:
                await self.conversation_connections[conversation_id].send_json(message)
                print(f"[WebSocket] ✅ Message sent to conversation {conversation_id}")
                return True
            except Exception as e:
                print(f"[WebSocket] ❌ Failed to send: {e}")
                return False
        else:
            print(f"[WebSocket] ❌ Conversation {conversation_id} not in active connections")
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
    chatbot = db.query(database.Chatbot).filter(database.Chatbot.api_key == api_key).first()
    
    if not chatbot:
        await websocket.close(code=4001, reason="Invalid API key")
        return
    
    await websocket.accept()
    
    data = await websocket.receive_text()
    init_data = json.loads(data)
    
    session_id = init_data.get('session_id', f"{api_key}_{datetime.utcnow().timestamp()}")
    conversation_id = init_data.get('conversation_id')
    
    conversation = None
    history = []
    
    if conversation_id:
        conversation = db.query(database.Conversation).filter(
            database.Conversation.id == conversation_id,
            database.Conversation.chatbot_id == chatbot.id
        ).first()
        
        if conversation:
            messages = db.query(database.Message).filter(
                database.Message.conversation_id == conversation_id
            ).order_by(database.Message.created_at.desc()).limit(10).all()
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
        conversation = database.Conversation(
            chatbot_id=chatbot.id,
            session_id=session_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        await websocket.send_json({
            'type': 'complete',
            'conversation_id': conversation.id
        })
    
    manager.conversation_connections[conversation.id] = websocket
    print(f"[WebSocket] Conversation {conversation.id} connected, mode: {conversation.mode}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get('message', '')
            
            db_message = database.Message(
                conversation_id=conversation.id,
                role='user',
                content=user_message
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            db.refresh(conversation)
            
            if conversation.mode == "human":
                print(f"[Chat] User message in human mode, broadcasting to support...")
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
                    print(f"[Chat] ✅ User message broadcasted to ticket {conversation.ticket_id}")
                continue
            
            history.append({'role': 'user', 'content': user_message})
            
            full_response = ""
            async for chunk in chat_service.stream_chat(chatbot.id, user_message, history):
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
            
            db_response = database.Message(
                conversation_id=conversation.id,
                role='assistant',
                content=full_response
            )
            db.add(db_response)
            db.commit()
    
    except WebSocketDisconnect:
        if conversation.id in manager.conversation_connections:
            del manager.conversation_connections[conversation.id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if conversation.id in manager.conversation_connections:
            del manager.conversation_connections[conversation.id]

async def handle_support_websocket(websocket: WebSocket, ticket_id: int, support_email: str, db: Session):
    ticket = db.query(database.SupportTicket).filter(database.SupportTicket.id == ticket_id).first()
    
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
            
            db_message = database.Message(
                conversation_id=ticket.conversation_id,
                role='assistant',
                content=content,
                sender_type='support',
                sender_email=support_email
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            if ticket.status == "open":
                ticket.status = "in_progress"
                db.commit()
            
            message_obj = {
                'id': db_message.id,
                'role': 'assistant',
                'content': content,
                'sender_type': 'support',
                'sender_email': support_email,
                'created_at': db_message.created_at.isoformat()
            }
            
            await manager.broadcast_to_ticket(ticket_id, {
                'type': 'message',
                'message': message_obj
            })
            
            sent = await manager.send_to_conversation(ticket.conversation_id, {
                'type': 'human_message',
                'content': content,
                'sender_email': support_email,
                'timestamp': db_message.created_at.isoformat()
            })
            
            if sent:
                print(f"[Support] ✅ Message delivered to user in real-time")
            else:
                print(f"[Support] ⚠️ User not connected, message saved to DB only")
    
    except WebSocketDisconnect:
        manager.disconnect_support(websocket, ticket_id)
    except Exception as e:
        print(f"Support WebSocket error: {e}")
        manager.disconnect_support(websocket, ticket_id)

