import asyncio
import datetime
import json

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load sample customers from the JSON file


# PostgreSQL connection parameters
db_params = {
    "database": "smartspa",
    "user": "root",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}

# Load interests from the JSON file
with open("sampling/interests.json", "r", encoding="utf-8-sig") as f:
    interests = json.load(f)


async def create_and_insert_interests():
    # Create a connection pool
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Define the interests table
    metadata = MetaData()
    interests_table = Table(
        "interests",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("related_terms", Text, nullable=False),
        Column("status", String(50), default="published"),
        Column("created_at", DateTime, default=datetime.datetime.now),
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async with async_session() as session:
        for interest in interests:
            query = interests_table.insert().values(**interest)
            await session.execute(query)
        await session.commit()

    await engine.dispose()
    await session.close()


if __name__ == "__main__":
    asyncio.run(create_and_insert_interests())
    print("Interests inserted successfully.")
