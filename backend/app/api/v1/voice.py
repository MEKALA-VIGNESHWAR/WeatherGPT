from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.voice.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice Pipeline"])


class SpeechSynthesisRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en")
):
    try:
        content = await file.read()
        transcription = await voice_service.transcribe_audio(content, language=language or "en")
        return {
            "transcription": transcription,
            "language": language,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_voice(req: SpeechSynthesisRequest):
    try:
        return await voice_service.synthesize_speech(req.text, language=req.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
