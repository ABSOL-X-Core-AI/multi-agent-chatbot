import uuid
import logging
from sqlalchemy import select, update, text
from app.services.db_services.models import ChatHistory, ChatSession
from app.services.db_services.database import AsyncSessionLocal

logger = logging.getLogger("uvicorn.error")


async def create_session(session_id: str, title: str | None = None) -> ChatSession:
    """Create a new conversation thread."""
    thread_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        async with db.begin():
            db.add(
                ChatSession(
                    thread_id=thread_id,
                    session_id=session_id,
                    title=title or "New Conversation",
                )
            )

    logger.info(f"Created thread '{thread_id}' for session '{session_id}'")
    return {
        "thread_id": thread_id,
        "session_id": session_id,
        "title": title or "New Conversation",
    }


async def get_sessions(session_id: str) -> list[ChatSession]:
    """Get all non-deleted threads for a user (for the sidebar)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.session_id == session_id,
                ChatSession.is_deleted == False,
            )
            .order_by(ChatSession.created_at.desc())
        )
        rows = result.scalars().all()

    return [
        {
            "thread_id": r.thread_id,
            "title": r.title,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def save_message(
    thread_id: str,
    session_id: str,
    role: str,
    content: str,
) -> ChatHistory:
    """Append a single message to a thread."""

    message = ChatHistory(
        thread_id=thread_id,
        session_id=session_id,
        role=role,
        content=content,
    )
    async with AsyncSessionLocal() as db:
        async with db.begin():
            db.add(message)

    logger.info(f"Saved '{role}' message to thread '{thread_id}'")


async def load_chat_history(thread_id: str) -> list[dict]:
    """Load all messages for a thread, ordered oldest → newest."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                """
                SELECT role, content, created_at
                FROM chat_history
                WHERE thread_id = :thread_id
                ORDER BY created_at ASC
                """
            ),
            {"thread_id": thread_id},
        )
        rows = result.mappings().all()

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


async def delete_session(thread_id: str) -> None:
    """Soft delete a conversation thread."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            await db.execute(
                update(ChatSession)
                .where(ChatSession.thread_id == thread_id)
                .values(is_deleted=True)
            )

    logger.info(f"Soft deleted thread '{thread_id}'")


async def update_title(thread_id: str, title: str) -> None:
    """Update thread title."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            await db.execute(
                update(ChatSession)
                .where(ChatSession.thread_id == thread_id)
                .values(title=title)
            )

    logger.info(f"Updated title for thread '{thread_id}' to '{title}'")
