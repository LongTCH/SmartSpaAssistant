from typing import AsyncGenerator

from app.configs import env_config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# SQLAlchemy setup
engine = create_async_engine(
    env_config.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,  # Reduce pool size to avoid too many connections
    max_overflow=20,
    pool_timeout=60,  # Increase timeout
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_pre_ping=True,  # Verify connections before using them
)
# Create session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

# Dependency for route handlers - changed to be compatible with FastAPI dependency injection


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency for route handlers"""
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# For use in background tasks
def get_db_session():
    """Get a session for background tasks"""
    return async_session()  # The caller is responsible for closing the session


async def init_models():
    """Initialize models during application startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def shutdown_models():
    """Close all connections during application shutdown"""
    await engine.dispose()
