from pydantic import BaseModel
from agents.session import chat
from fastapi import APIRouter, HTTPException


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        reply = await chat(
            user_message=request.message,
            thread_id=request.thread_id,
        )
        return ChatResponse(reply=reply, thread_id=request.thread_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
