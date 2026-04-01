import logging
from .main_agent import main_agent
from app.services.db_services.db_operations import (
    load_chat_history,
    save_message,
)
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger("uvicorn.error")


def _build_messages(history: list[dict]) -> list:
    """Convert list of dicts from DB into LangChain message objects."""
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


async def chat(user_message: str, thread_id: str) -> str:
    # Load this thread's full history from PostgreSQL
    history = await load_chat_history(thread_id)
    logger.info(f"Loaded {len(history)} messages for thread '{thread_id}'")

    # Build LangChain message list from DB rows
    messages = _build_messages(history)

    # Append the new user message
    messages.append(HumanMessage(content=user_message))

    # Run the agent with full history — it sees all past context
    result = await main_agent.ainvoke({"messages": messages})
    reply = result["messages"][-1].content

    # Persist both the user message and reply to PostgreSQL
    await save_message(thread_id=thread_id, role="user", content=user_message)
    await save_message(thread_id=thread_id, role="assistant", content=reply)

    logger.info(f"Saved 2 messages for thread '{thread_id}'")
    return reply
