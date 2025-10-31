from fastapi import WebSocket
import json
import base64
from faster_whisper import WhisperModel
from pydub import AudioSegment
import numpy as np
import tempfile
import os
import wave

whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe_audio_file(audio_path: str, language: str = None) -> str:
    """Transcribe audio file using Whisper. Auto-detects language if not specified."""
    try:
        segments, info = whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False
        )
        
        transcription = " ".join([segment.text.strip() for segment in segments])
        detected_lang = info.language if hasattr(info, 'language') else 'unknown'
        
        if transcription:
            print(f"📝 Transcribed ({detected_lang}): {transcription[:100]}...")
        return transcription.strip()
    
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""

async def handle_transcription_only(websocket: WebSocket, api_key: str):
    """Real-time transcription only - no LLM response"""
    from starlette.websockets import WebSocketState
    
    await websocket.accept()
    
    audio_chunks = []
    chunk_count = 0
    
    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            
            if data.get("type") == "audio_chunk":
                audio_base64 = data["audio"]
                audio_bytes = base64.b64decode(audio_base64)
                audio_chunks.append(audio_bytes)
                chunk_count += 1
                
                # Process every 2 chunks (4 seconds of audio) for faster real-time feedback
                if chunk_count >= 2:
                    transcription = await transcribe_webm_audio(audio_chunks)
                    if transcription and websocket.client_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_json({
                                "type": "transcription",
                                "text": transcription
                            })
                        except:
                            break
                    audio_chunks = []
                    chunk_count = 0
            
            elif data.get("type") == "stop":
                # Process remaining audio
                if audio_chunks and websocket.client_state == WebSocketState.CONNECTED:
                    transcription = await transcribe_webm_audio(audio_chunks)
                    if transcription:
                        try:
                            await websocket.send_json({
                                "type": "transcription",
                                "text": transcription
                            })
                        except:
                            pass
                break
    
    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"❌ Transcription error: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except:
                pass

async def transcribe_webm_audio(audio_chunks: list) -> str:
    """Transcribe webm audio using Whisper"""
    temp_webm = None
    temp_wav = None
    
    try:
        # Combine all chunks
        combined_audio = b"".join(audio_chunks)
        
        # Check if we have enough audio data
        if len(combined_audio) < 5000:
            return ""
        
        # Save webm to temp file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            temp_webm = f.name
            f.write(combined_audio)
        
        try:
            # Convert webm to wav using pydub
            audio = AudioSegment.from_file(temp_webm, format="webm")
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # Export as WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                audio.export(temp_wav, format="wav")
            
            return transcribe_audio_file(temp_wav, language="en")
        
        except Exception as decode_error:
            print(f"⚠️ Webm decode failed: {str(decode_error)[:100]}")
            return ""
    
    except Exception as e:
        print(f"❌ Whisper transcription error: {e}")
        return ""
    
    finally:
        for temp_file in [temp_webm, temp_wav]:
            if temp_file:
                try:
                    os.unlink(temp_file)
                except:
                    pass

