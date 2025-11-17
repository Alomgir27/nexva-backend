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

