import asyncio
from typing import Optional
from kokoro_service import kokoro_service

class NeuralTTSService:
    def __init__(self):
        self.kokoro = kokoro_service
        if self.kokoro.is_available:
            print(f"✅ Kokoro-82M initialized successfully")
        else:
            print(f"ℹ️ Kokoro TTS will load on first use")
    
    async def generate_speech_async(
        self, 
        text: str, 
        voice: str = None, 
        speaker_wav: Optional[str] = None,
        language: str = "en"
    ) -> bytes:
        return await self.kokoro.generate_speech_async(text, voice=voice, language=language)
    
    def generate_speech(
        self, 
        text: str, 
        voice: str = None,
        speaker_wav: Optional[str] = None,
        language: str = "en"
    ) -> bytes:
        return self.kokoro.generate_speech(text, voice=voice, language=language)

neural_tts = NeuralTTSService()

