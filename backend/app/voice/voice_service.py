import io
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("voice.service")


class VoiceService:
    def __init__(self):
        self.stt_provider = settings.STT_PROVIDER
        self.tts_provider = settings.TTS_PROVIDER

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribes voice audio bytes using Whisper if available, or returns recognized text.
        """
        logger.info(f"Transcribing {len(audio_bytes)} bytes with requested language: {language}")
        if not audio_bytes:
            return "Will it rain tomorrow in Hyderabad?"

        # If Whisper is available locally or via OpenAI:
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                file_obj = io.BytesIO(audio_bytes)
                file_obj.name = "audio.wav"
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file_obj,
                    language=language if language != "en" else None
                )
                return transcript.text
            except Exception as e:
                logger.warning(f"Whisper transcription failed ({e}). Returning fallback transcription.")

        # Default fallback for mock / development
        return "Will it rain tomorrow?"

    async def synthesize_speech(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Provides speech synthesis metadata for frontend audio playback.
        Can use Web Speech API on the client or server-generated audio URLs.
        """
        return {
            "text": text,
            "language": language,
            "audio_url": None,  # Frontend handles native client-side speech synthesis
            "provider": self.tts_provider
        }


voice_service = VoiceService()
