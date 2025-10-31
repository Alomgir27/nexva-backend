import os
from typing import Optional
from kokoro import KPipeline
import soundfile as sf
from io import BytesIO
import torch

_model_instance = None

class KokoroService:
    def __init__(self):
        global _model_instance
        if _model_instance is not None:
            self.pipeline = _model_instance
            self.device = self.pipeline.device if hasattr(self.pipeline, 'device') else 'cpu'
            print(f"✅ Using cached Kokoro model on {self.device}")
        else:
            self.pipeline = None
            self.device = 'cpu'
            self._initialize_model()
    
    def _initialize_model(self):
        global _model_instance
        
        if torch.cuda.is_available():
            try:
                self.device = 'cuda'
                print(f"🚀 Loading Kokoro-82M on GPU...")
                self.pipeline = KPipeline(lang_code='a', device='cuda')
                _model_instance = self.pipeline
                print(f"✅ Kokoro-82M loaded on GPU (82M params)")
                return
            except Exception as e:
                print(f"⚠️ GPU loading failed, falling back to CPU: {e}")
        
        try:
            self.device = 'cpu'
            print(f"🚀 Loading Kokoro-82M on CPU...")
            self.pipeline = KPipeline(lang_code='a', device='cpu')
            _model_instance = self.pipeline
            print(f"✅ Kokoro-82M loaded on CPU (82M params)")
        except Exception as e:
            print(f"❌ Kokoro initialization failed: {e}")
            self.pipeline = None
    
    async def generate_speech_async(
        self, 
        text: str, 
        voice: str = None,
        speaker_wav: Optional[str] = None,
        language: str = "en",
        voice_id: str = None
    ):
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_speech,
            text,
            voice,
            speaker_wav,
            language,
            voice_id
        )
    
    def generate_speech(
        self, 
        text: str, 
        voice: str = None,
        speaker_wav: Optional[str] = None,
        language: str = "en",
        voice_id: str = None
    ) -> bytes:
        if not self.pipeline:
            raise Exception("Kokoro model not initialized")
        
        try:
            # Map our voice IDs to Kokoro voices
            kokoro_voice = self._get_kokoro_voice(voice_id or voice)
            
            # Generate audio
            generator = self.pipeline(text, voice=kokoro_voice)
            
            # Get first (and usually only) audio chunk
            audio_data = None
            for _, _, audio in generator:
                audio_data = audio
                break  # Take first chunk only for faster response
            
            if audio_data is None:
                raise Exception("No audio generated")
            
            # Convert to WAV bytes
            output = BytesIO()
            sf.write(output, audio_data, 24000, format='WAV')
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            raise Exception(f"Kokoro generation failed: {str(e)}")
    
    def _get_kokoro_voice(self, voice_id: str = None) -> str:
        """Map our voice IDs to Kokoro voice names"""
        voice_map = {
            'female-1': 'af_heart',
            'female-2': 'af_nova',
            'female-3': 'af_sarah',
            'female-4': 'af_nicole',
            'female-5': 'af_sky',
            'male-1': 'am_adam',
            'male-2': 'am_michael',
            'male-3': 'af_bella',  # Kokoro has limited male voices
            'male-4': 'af_nicole',
            'male-5': 'af_heart',
        }
        return voice_map.get(voice_id, 'af_heart')
    
    @property
    def is_available(self) -> bool:
        return self.pipeline is not None

kokoro_service = KokoroService()

