import asyncio
import datetime
import json

from faker import Faker
from sqlalchemy import Column, DateTime, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# đọc danh sách customer từ sampling/customers.json
with open("sampling/customers.json", "r", encoding="utf-8") as f:
    sample_customers = json.load(f)

# đọc danh sách các đoạn chat từ sampling/file_chats.json
with open("sampling/file_chats.json", "r", encoding="utf-8-sig") as f:
    sample_conversations = json.load(f)

db_params = {
    "database": "smartspa",
    "user": "root",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}


async def create_and_insert_conversations():
    # bảng conversations có các trường id, guest_id, message, created_at
    # tạo bảng conversations nếu chưa tồn tại
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    metadata = MetaData()
    chats = Table(
        "chats",
        metadata,
        Column("id", String, primary_key=True),
        Column("guest_id", String, nullable=False),
        Column("content", JSONB, nullable=False),
        Column("created_at", DateTime, default=datetime.datetime.now),
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async with async_session() as session:
        # Select a random customer to associate with the conversation
        for i, customer in enumerate(sample_customers):
            guest_id = customer["id"]
            last_message_at = datetime.datetime.strptime(
                customer["last_message_at"], "%Y-%m-%d %H:%M:%S"
            )
            # Giả sử có nhiều đoạn chat khác nhau
            conversation = sample_conversations[i % len(sample_conversations)]
            conversation = list(conversation.values())[0]
            # Insert conversation for this customer
            for t, message in enumerate(conversation):
                query = chats.insert().values(
                    id=Faker().uuid4(),
                    guest_id=guest_id,
                    content=message,
                    # minus time delta 5s for each message
                    created_at=last_message_at
                    - datetime.timedelta(seconds=(len(conversation) - t - 1) * 5),
                )
                await session.execute(query)

            # Get the last message object directly for storing as JSONB
            last_message = conversation[-1]

            # Update the last message for this customer as JSONB
            from sqlalchemy import text

            query = text(
                """
                UPDATE guests
                SET last_message = :last_message
                WHERE id = :guest_id
            """
            )
            await session.execute(
                query, {"last_message": json.dumps(last_message), "guest_id": guest_id}
            )
        await session.commit()

    await engine.dispose()
    print("Conversations created and inserted successfully.")


if __name__ == "__main__":
    asyncio.run(create_and_insert_conversations())
