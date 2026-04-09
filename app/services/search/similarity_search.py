import logging
from app.services.embeddings import embed_query
from app.services.db_services.db_operations import search_similar_chunks
from langfuse import get_client

logger = logging.getLogger("uvicorn.error")
langfuse = get_client()


async def similarity_search(
    query: str,
    k: int = 5,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Question cannot be empty.")

    logger.info(f"Searching for: '{query}' (k={k})")

    with langfuse.start_as_current_observation(
        as_type="span", name="similarity-search", input={"query": query, "k": k}
    ) as span:

        # Embedding
        with langfuse.start_as_current_observation(
            as_type="span", name="embedding", input={"query": query}
        ) as embed_span:
            try:
                query_vector = embed_query(query)
                embed_span.update(output={"vector_dim": len(query_vector)})
            except Exception as e:
                embed_span.update(level="Error", status_message=str(e))
                raise

        # Vector Search
        with langfuse.start_as_current_observation(
            as_type="span",
            name="vector-search",
            input={"k": k},
        ) as search_span:
            try:
                results = await search_similar_chunks(
                    query_embedding=query_vector,
                    k=k,
                )
                search_span.update(
                    output={
                        "result_count": len(results),
                        "top_similarity": results[0]["similarity"] if results else 0,
                    }
                )
            except Exception as e:
                search_span.update(level="Error", status_message=str(e))
                raise

        span.update(output={"results_count": len(results)})

    logger.info(f"Returned {len(results)} results for query '{query}'")
    return results
