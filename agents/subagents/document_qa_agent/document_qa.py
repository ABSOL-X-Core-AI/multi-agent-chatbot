import logging
from agents.llm import get_llm
from langchain.tools import tool
from langchain.agents import create_agent
from app.services.search.similarity_search import similarity_search

logger = logging.getLogger("uvicorn.error")


@tool(description="Search uploaded documents using pgvector similarity search.")
async def search_documents(query: str) -> str:
    results: list[dict] = await similarity_search(query=query, k=5)

    if not results:
        return "No relevant content found in the uploaded documents."

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[Source {i}]\n"
            f"File     : {r['filename']}\n"
            f"Chunk    : {r['chunk_index']}\n"
            f"Similarity: {r['similarity']:.4f}\n"
            f"Content  : {r['content']}"
        )

    return "\n\n---\n\n".join(parts)


_llm = get_llm(temperature=0.2)

DOCUMENT_QA_PROMPT = """"  You are a document question-answering specialist. 
    You have access to a pgvector similarity search over the user's uploaded documents.

        Rules:
            - ALWAYS call search_documents first before answering
            - Answer using ONLY the retrieved content — never invent information
            - Always mention the source filename when citing information
            - If all similarity scores are below 0.5, warn the user the match may be weak
            - If no relevant content is found, say so clearly — do not guess
            - Your final message must be a complete, self-contained answer — the supervisor only sees your last message, not your tool calls
"""

document_qa_subagent = create_agent(
    model=_llm,
    tools=[search_documents],
    system_prompt=DOCUMENT_QA_PROMPT,
)


@tool(
    "document_qa_agent",
    description=(
        "Use this when the user asks ANY question that could be answered from "
        "their uploaded documents. This includes: asking what a document says, "
        "finding specific information in files, summarising uploaded content, "
        "or any factual question where the answer may exist in their documents. "
        "When in doubt, prefer calling this tool."
    ),
)
async def call_document_qa_agent(query: str) -> str:
    """Routes document questions to the document QA subagent."""
    logger.info(f"document_qa_agent called with: '{query}'")
    result = await document_qa_subagent.ainvoke(
        {"messages": [{"role": "user", "content": query}]}
    )
    return result["messages"][-1].content
