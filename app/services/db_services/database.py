import os
import logging
from dotenv import load_dotenv
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

load_dotenv()

logger = logging.getLogger("uvicorn.error")


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=0,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables():
    from app.services.db_services.models import Base

    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes that need a DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def close_engine():
    """Dispose the engine on app shutdown."""
    await engine.dispose()
