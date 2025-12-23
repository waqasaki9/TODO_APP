"""
Database module for PostgreSQL connection and session management.
Uses SQLAlchemy async for non-blocking database operations.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Convert postgresql:// to postgresql+asyncpg:// for async support
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Async engine for FastAPI endpoints
async_engine = create_async_engine(
    async_database_url,
    echo=True,  # Set to False in production
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for LangChain tools (some operations need sync)
sync_engine = create_engine(
    settings.database_url,
    echo=True
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Base class for all models
Base = declarative_base()


async def get_async_session() -> AsyncSession:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        yield session


def get_sync_session():
    """Get sync database session for tools."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
