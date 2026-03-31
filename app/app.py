import logging
from fastapi import FastAPI
from sqlalchemy import text
from .routes.user import search
from .routes.user import upload
from contextlib import asynccontextmanager
from app.services.db_services.database import engine, create_tables, close_engine

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_tables()
    logger.info("Database tables created/verified")

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connected and verified")
    yield
    await close_engine()
    logger.info("Database disconnected")


app = FastAPI(
    title="Multi Agent Chatbot API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(upload.router, prefix="/chatbot/v1", tags=["upload"])
app.include_router(search.router, prefix="/chatbot/v1", tags=["search"])


@app.get("/health", tags=["health"])
async def health_check():
    async with engine.connect() as conn:
        db_version = await conn.scalar(text("SELECT version()"))
    return {
        "status": "ok",
        "database": "connected",
        "db_version": db_version,
    }
