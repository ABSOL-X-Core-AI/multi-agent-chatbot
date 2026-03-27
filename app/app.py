import logging
from fastapi import FastAPI
from .routes import upload
from contextlib import asynccontextmanager
from .services.database import get_pool, close_pool

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    logger.info("Database connected and verified")
    yield
    await close_pool()
    logger.info("Database disconnected")


app = FastAPI(
    title="Multi Agent Chatbot API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(upload.router, prefix="/chatbot/v1", tags=["upload"])


@app.get("/health", tags=["health"])
async def health_check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        db_version = await conn.fetchval("SELECT version()")
    return {
        "status": "ok",
        "database": "connected",
        "db_version": db_version,
    }
