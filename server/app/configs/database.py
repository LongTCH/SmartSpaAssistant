import re
from typing import AsyncGenerator

import asyncpg
from app.configs import env_config
from scripts.init_sql import create_custom_functions_and_triggers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Extract database name from DATABASE_URL
match = re.search(
    r"postgres(?:ql)?:\/\/(?:.*):(?:.*)@(?:.*):(?:\d+)\/([a-zA-Z0-9_]+)",
    env_config.DATABASE_URL,
)
db_name = match.group(1) if match else "smartspa"


async def ensure_database_exists():
    """Create the database if it doesn't exist"""
    # Convert SQLAlchemy URL to asyncpg compatible URL
    asyncpg_url = env_config.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    )

    # Create a connection string to the default postgres database
    conn_string = asyncpg_url.rsplit("/", 1)[0] + "/postgres"

    # Connect to the default database
    try:
        conn = await asyncpg.connect(conn_string)

        # Check if our database exists
        exists = await conn.fetchval(
            f"SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )

        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            # Close any existing connections to the database we want to drop
            await conn.execute(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = $1
                """,
                db_name,
            )

            # Create the database
            await conn.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")

        await conn.close()
    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        raise


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
    # Ensure the database exists before initializing models
    await ensure_database_exists()

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Convert SQLAlchemy URL to asyncpg compatible URL
    asyncpg_url = env_config.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    )

    # Connect để tạo các functions, triggers, và set up PGroonga
    conn = await asyncpg.connect(asyncpg_url)
    try:
        print("Thiết lập PGroonga và các triggers...")
        await create_custom_functions_and_triggers(conn)
        print("Thiết lập PGroonga và các triggers hoàn tất")
    finally:
        await conn.close()


async def shutdown_models():
    """Close all connections during application shutdown"""
    await engine.dispose()
