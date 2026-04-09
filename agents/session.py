import logging
from .main_agent import main_agent
from app.services.db_services.db_operations import load_chat_history, save_message
from langchain_core.messages import HumanMessage, AIMessage
from langfuse.langchain import CallbackHandler
from langfuse import get_client, observe, propagate_attributes

logger = logging.getLogger("uvicorn.error")
langfuse = get_client()


def _build_messages(history: list[dict]) -> list:
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


@observe(name="chat-session")
async def chat(user_message: str, session_id: str, thread_id: str) -> str:

    with propagate_attributes(
        session_id=session_id,
        tags=["chat"],
        metadata={"thread_id": thread_id},
    ):
        # Load history
        history = await load_chat_history(session_id, thread_id)
        logger.info(
            f"Loaded {len(history)} messages for session '{session_id}', thread '{thread_id}'"
        )

        # Build messages
        messages = _build_messages(history)
        messages.append(HumanMessage(content=user_message))

        # Callback handler — auto-traces all LLM calls and tool calls
        langfuse_handler = CallbackHandler()

        # Run agent
        result = await main_agent.ainvoke(
            {"messages": messages},
            config={"callbacks": [langfuse_handler]},
        )
        reply = result["messages"][-1].content

        # Save to DB
        await save_message(
            session_id=session_id,
            thread_id=thread_id,
            role="user",
            content=user_message,
        )
        await save_message(
            session_id=session_id,
            thread_id=thread_id,
            role="assistant",
            content=reply,
        )

        logger.info(f"Saved messages for session '{session_id}', thread '{thread_id}'")
        return reply
