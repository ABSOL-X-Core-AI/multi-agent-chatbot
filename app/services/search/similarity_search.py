import logging
from app.services.embeddings import embed_query
from app.services.db_services.db_operations import search_similar_chunks

logger = logging.getLogger("uvicorn.error")


async def similarity_search(
    query: str,
    k: int = 5,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Question cannot be empty.")

    logger.info(f"Searching for: '{query}' (k={k})")

    # Embed the question
    query_vector = embed_query(query)

    # Search pgvector
    results = await search_similar_chunks(
        query_embedding=query_vector,
        k=k,
    )

    logger.info(f"Returned {len(results)} results for query '{query}'")
    return results
