from typing import Optional
from kokoro import KPipeline
import soundfile as sf
from io import BytesIO
import torch
import asyncio

_model_instance = None
_model_init_lock = asyncio.Lock()


class KokoroService:
    def __init__(self):
        global _model_instance
        self.pipeline = _model_instance
        self.device = self.pipeline.device if self.pipeline and hasattr(self.pipeline, 'device') else 'cpu'
        if self.pipeline:
            print(f"✅ Using cached Kokoro model on {self.device}")
    
    async def _ensure_model(self):
        global _model_instance

        if self.pipeline:
            return

        async with _model_init_lock:
            if _model_instance is not None:
                self.pipeline = _model_instance
                self.device = self.pipeline.device if hasattr(self.pipeline, 'device') else 'cpu'
                return

            try:
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                print(f"🚀 Loading Kokoro-82M on {device.upper()}...")
                
                self.pipeline = KPipeline(lang_code='a', device=device)
                self.device = device
                _model_instance = self.pipeline
                
                # Warmup inference
                try:
                    list(self.pipeline("Hi", voice='af_heart'))
                    print(f"🔥 Warmup complete")
                except:
                    pass
                
                print(f"✅ Kokoro-82M ready on {device.upper()}")
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
        await self._ensure_model()
        if not self.pipeline:
            raise Exception("Kokoro model not initialized")
        
        kokoro_voice = self._get_kokoro_voice(voice_id or voice)
        generator = self.pipeline(text, voice=kokoro_voice)
        
        audio_data = None
        for _, _, audio in generator:
            audio_data = audio
            break
        
        if audio_data is None:
            raise Exception("No audio generated")
        
        output = BytesIO()
        sf.write(output, audio_data, 24000, format='WAV')
        output.seek(0)
        return output.read()
    
    def _get_kokoro_voice(self, voice_id: str = None) -> str:
        voice_map = {
            'female-1': 'af_heart',
            'female-2': 'af_nova',
            'female-3': 'af_sarah',
            'female-4': 'af_nicole',
            'female-5': 'af_sky',
            'male-1': 'am_adam',
            'male-2': 'am_michael',
            'male-3': 'af_bella',
            'male-4': 'af_nicole',
            'male-5': 'af_heart',
        }
        return voice_map.get(voice_id, 'af_heart')
    
    @property
    def is_available(self) -> bool:
        return self.pipeline is not None

async def preload_kokoro():
    """Multi-worker mode: each worker lazy-loads Kokoro on first TTS request"""
    pass

kokoro_service = KokoroService()

