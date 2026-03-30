from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.search.similarity_search import similarity_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    k: int = 5


class ChunkResult(BaseModel):
    filename: str
    chunk_index: int
    content: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    k: int
    results: list[ChunkResult]


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    try:
        results = await similarity_search(
            query=request.query,
            k=request.k,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    return SearchResponse(
        query=request.query,
        k=request.k,
        results=results,
    )
