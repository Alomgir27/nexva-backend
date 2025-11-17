import asyncio
from typing import Optional
from app.services.kokoro_service import kokoro_service

class NeuralTTSService:
    def __init__(self):
        self.kokoro = kokoro_service
        if self.kokoro.is_available:
            print(f"✅ Kokoro-82M initialized successfully")
        else:
            print(f"⚠️ Kokoro not available")
    
    async def generate_speech_async(
        self, 
        text: str, 
        voice: str = None, 
        speaker_wav: Optional[str] = None,
        language: str = "en"
    ) -> bytes:
        if not self.kokoro.is_available:
            raise Exception("Kokoro not available")
        
        return await self.kokoro.generate_speech_async(text, voice=voice, language=language)
    
    def generate_speech(
        self, 
        text: str, 
        voice: str = None,
        speaker_wav: Optional[str] = None,
        language: str = "en"
    ) -> bytes:
        if not self.kokoro.is_available:
            raise Exception("Kokoro not available")
        
        return self.kokoro.generate_speech(text, voice=voice, language=language)

neural_tts = NeuralTTSService()

