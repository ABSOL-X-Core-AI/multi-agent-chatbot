from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.db_services.chat_operations import (
    create_session,
    get_sessions,
    load_chat_history,
    delete_session,
    update_title,
)

router = APIRouter()


class CreateSessionRequest(BaseModel):
    session_id: str
    # title: str | None = None


class UpdateTitleRequest(BaseModel):
    title: str


@router.post("/sessions")
async def new_session(req: CreateSessionRequest):
    """Create a new conversation thread."""
    try:
        return await create_session(req.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def list_sessions(session_id: str):
    """Get all threads for a user — for the sidebar."""
    try:
        return await get_sessions(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{thread_id}/messages")
async def list_messages(thread_id: str):
    """Get all messages in a conversation."""
    try:
        return await load_chat_history(thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{thread_id}")
async def remove_session(thread_id: str):
    """Soft delete a conversation."""
    try:
        await delete_session(thread_id)
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{thread_id}/title")
async def rename_session(thread_id: str, req: UpdateTitleRequest):
    """Rename a conversation thread."""
    try:
        await update_title(thread_id, req.title)
        return {"message": "Title updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
