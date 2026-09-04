import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse, ChatFeedbackRequest
from app.ai.orchestrator import orchestrator
from app.core.database import get_db
from app.models.models import Conversation, Message, Feedback
from app.core.logging import get_logger

logger = get_logger("api.chat")
router = APIRouter(prefix="/chat", tags=["Conversational Weather Intelligence"])


@router.post("", response_model=ChatResponse)
async def chat_query(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        resp = await orchestrator.process_query(req)
        
        # Persist conversation and messages to DB
        conv = db.query(Conversation).filter(Conversation.id == resp.conversation_id).first()
        if not conv:
            conv = Conversation(id=resp.conversation_id, title=req.message[:50])
            db.add(conv)
            db.commit()

        # Save user message
        db.add(Message(
            id=req.conversation_id or resp.conversation_id,
            conversation_id=resp.conversation_id,
            sender="user",
            content=req.message
        ))

        # Save assistant message
        db.add(Message(
            id=resp.message_id,
            conversation_id=resp.conversation_id,
            sender="assistant",
            content=resp.answer,
            structured_data=resp.model_dump(mode="json")
        ))
        db.commit()

        return resp
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """
    Streams grounded response in SSE chunks after tool validation is completed.
    """
    resp = await orchestrator.process_query(req)
    
    async def event_generator():
        # First send tool completion event
        yield f"event: tools\ndata: {json.dumps([t.model_dump() for t in resp.tools_called])}\n\n"
        await asyncio.sleep(0.05)

        # Send structured metadata event
        meta_payload = {
            "conversation_id": resp.conversation_id,
            "message_id": resp.message_id,
            "location": resp.location,
            "risk_level": resp.risk_level.value,
            "confidence": resp.confidence,
            "sources": resp.sources,
            "weather_summary": resp.weather_summary.model_dump()
        }
        yield f"event: metadata\ndata: {json.dumps(meta_payload)}\n\n"

        # Stream text words with natural typing cadence
        words = resp.answer.split(" ")
        for i, word in enumerate(words):
            yield f"event: token\ndata: {json.dumps({'token': word + (' ' if i < len(words) - 1 else '')})}\n\n"
            await asyncio.sleep(0.02)

        # Final complete message
        yield f"event: complete\ndata: {json.dumps(resp.model_dump())}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/feedback")
def submit_feedback(req: ChatFeedbackRequest, db: Session = Depends(get_db)):
    fb = Feedback(
        message_id=req.message_id,
        is_helpful=req.is_helpful,
        was_accurate=req.was_accurate,
        comment=req.comment,
        corrected_info=req.corrected_info
    )
    db.add(fb)
    db.commit()
    return {"status": "success", "message": "Feedback recorded. Thank you for helping improve WeatherGPT."}
