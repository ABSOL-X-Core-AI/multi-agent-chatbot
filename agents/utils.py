import logging
from .llm import get_llm

logger = logging.getLogger("uvicorn.error")

_llm = get_llm(temperature=0.3)


async def generate_title(user_message: str) -> str:
    """Generate a short conversation title from the first user message."""
    try:
        response = await _llm.ainvoke(
            f"Generate a short 4-6 word title for a conversation that starts "
            f"with this message. Reply with only the title, no punctuation, no quotes:\n\n"
            f"{user_message}"
        )
        return response.content.strip()
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        return "New Conversation"
