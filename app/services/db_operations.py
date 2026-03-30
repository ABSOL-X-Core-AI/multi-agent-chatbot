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


async def search_similar_chunks(
    query_embedding: list[float],
    k: int = 5,
) -> list[dict]:
    # Find top-k most similar chunks to the query embedding.
    pool = await get_pool()

    # pgvector's <-> operator = cosine distance
    # 1 - cosine distance = cosine similarity
    query = """
        SELECT
            filename,
            chunk_index,
            content,
            1 - (embedding <=> $1::vector) AS similarity
        FROM documents
        ORDER BY embedding <=> $1::vector
        LIMIT $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, str(query_embedding), k)

    return [
        {
            "filename": row["filename"],
            "chunk_index": row["chunk_index"],
            "content": row["content"].replace("\n", " ").strip(),
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]
