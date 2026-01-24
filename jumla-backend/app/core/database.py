"""
app/core/database.py
Async database engine and session management
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

# -----------------------------
# Async Engine
# -----------------------------
engine = create_async_engine(
    settings.DATABASE_URL,  # MUST be postgresql+asyncpg://
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"ssl": True},
)

# -----------------------------
# Session Factory
# -----------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -----------------------------
# FastAPI Dependency
# -----------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# -----------------------------
# Context Manager (scripts, jobs)
# -----------------------------

@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# -----------------------------
# Lifecycle Hooks
# -----------------------------

async def init_db() -> None:
    """
    Initialize database resources.
    NOTE: Use Alembic for schema changes.
    """
    from app.models import Base

    async with engine.begin() as conn:
        # PostgreSQL UUID extension
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

        if settings.ENVIRONMENT == "development":
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")

async def close_db() -> None:
    await engine.dispose()
    logger.info("Database connections closed")
