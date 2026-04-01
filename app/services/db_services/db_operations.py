import logging
from sqlalchemy import delete, text
from app.services.db_services.models import Document
from app.services.db_services.models import ChatHistory
from app.services.db_services.database import AsyncSessionLocal

logger = logging.getLogger("uvicorn.error")


async def save_document_chunks(
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    # Save all chunks and embeddings to pgvector.

    rows = [
        Document(
            filename=filename,
            chunk_index=i,
            content=chunk,
            embedding=embedding,
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(Document).where(Document.filename == filename))
            session.add_all(rows)

    logger.info(f"Saved {len(rows)} chunks for '{filename}'")
    return len(rows)


async def search_similar_chunks(
    query_embedding: list[float],
    k: int = 5,
) -> list[dict]:
    # Find top-k most similar chunks to the query embedding.

    # pgvector's <-> operator = cosine distance
    # 1 - cosine distance = cosine similarity
    sql = text(
        """
        SELECT
            filename,
            chunk_index,
            content,
            1 - (embedding <=> :embedding ::vector) AS similarity
        FROM documents
        ORDER BY embedding <=> :embedding ::vector
        LIMIT :k
    """
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            sql,
            {"embedding": str(query_embedding), "k": k},
        )
        rows = result.mappings().all()

    return [
        {
            "filename": row["filename"],
            "chunk_index": row["chunk_index"],
            "content": row["content"].replace("\n", " ").strip(),
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]


async def load_chat_history(thread_id: str) -> list[dict]:
    """
    Load all messages for a thread, ordered oldest → newest.
    Returns list of dicts: [{"role": "user", "content": "..."}]
    """

    async with AsyncSessionLocal() as session:
        sql = text(
            """
            SELECT
                role, content 
            FROM chat_history
            WHERE thread_id = :thread_id
            ORDER BY created_at ASC
            """
        )

        result = await session.execute(
            sql,
            {"thread_id": thread_id},
        )

        rows = result.mappings().all()

    return [{"role": row["role"], "content": row["content"]} for row in rows]


async def save_message(thread_id: str, role: str, content: str):
    """
    Save a single message to chat history.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(
                ChatHistory(
                    thread_id=thread_id,
                    role=role,
                    content=content,
                )
            )
