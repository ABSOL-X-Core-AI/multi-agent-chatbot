import logging
from app.services.database import get_pool

logger = logging.getLogger("uvicorn.error")


async def save_document_chunks(
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    # Save all chunks and embeddings to pgvector.
    pool = await get_pool()

    rows = [
        (filename, i, chunk, str(embedding))
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM documents WHERE filename = $1", filename)

            await conn.executemany(
                """
                INSERT INTO documents (filename, chunk_index, content, embedding)
                VALUES ($1, $2, $3, $4::vector)
                """,
                rows,
            )

    logger.info(f"Saved {len(rows)} chunks for '{filename}'")
    return len(rows)
