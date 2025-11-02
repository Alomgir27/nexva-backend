from typing import Optional
from kokoro import KPipeline
import soundfile as sf
from io import BytesIO
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor

_model_instance = None
_model_init_lock = asyncio.Lock()
_tts_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="tts")


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

            loop = asyncio.get_event_loop()
            try:
                self.device = 'cpu'
                print("🚀 Loading Kokoro-82M on CPU...")
                self.pipeline = await loop.run_in_executor(
                    None, lambda: KPipeline(lang_code='a', device='cpu')
                )
                _model_instance = self.pipeline
                print("✅ Kokoro-82M loaded on CPU (82M params)")
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
        if not self.pipeline:
            await self._ensure_model()
            if not self.pipeline:
                raise Exception("Kokoro model not initialized")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _tts_executor,
            self._generate_audio,
            text,
            voice_id or voice
        )
    
    def _generate_audio(self, text: str, voice_id: str = None) -> bytes:
        kokoro_voice = self._get_kokoro_voice(voice_id)
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

async def preload_kokoro():
    """Preload Kokoro model at startup"""
    global _model_instance
    if _model_instance is None:
        loop = asyncio.get_event_loop()
        try:
            print("🚀 Loading Kokoro-82M on CPU...")
            _model_instance = await loop.run_in_executor(
                None, lambda: KPipeline(lang_code='a', device='cpu')
            )
            print("✅ Kokoro-82M loaded on CPU (82M params)")
        except Exception as e:
            print(f"❌ Kokoro preload failed: {e}")
    
    kokoro_service.pipeline = _model_instance
    kokoro_service.device = _model_instance.device if _model_instance and hasattr(_model_instance, 'device') else 'cpu'

kokoro_service = KokoroService()

