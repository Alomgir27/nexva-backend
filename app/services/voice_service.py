import asyncio
import subprocess
import tempfile
import os
from pathlib import Path

class VoiceService:
    def __init__(self):
        self.neutts_available = False
        self._check_neutts()
    
    def _check_neutts(self):
        try:
            result = subprocess.run(['which', 'neutts'], capture_output=True, text=True)
            self.neutts_available = result.returncode == 0
        except:
            self.neutts_available = False
    
    async def text_to_speech(self, text: str) -> bytes:
        if not self.neutts_available:
            return await self._fallback_tts(text)
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            process = await asyncio.create_subprocess_exec(
                'neutts',
                '--text', text,
                '--output', output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                os.unlink(output_path)
                return audio_data
            
            return await self._fallback_tts(text)
        
        except Exception as e:
            print(f"NeuTTS error: {e}")
            return await self._fallback_tts(text)
    
    async def _fallback_tts(self, text: str) -> bytes:
        return b''

voice_service = VoiceService()

