import asyncio
import datetime
import json
import uuid

import asyncpg
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

with open("sampling/customers.json", "r", encoding="utf-8") as f:
    sample_customers = json.load(f)

# PostgreSQL connection parameters
db_params = {
    "database": "smartspa",
    "user": "root",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}


async def create_and_insert_guests():
    # Create a connection pool
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"

    # Create engine
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Create tables if they don't exist
        metadata = MetaData()

        # Define the guest_infos table - không có provider và account_name
        guest_infos = Table(
            "guest_infos",
            metadata,
            Column("id", String, primary_key=True, default=str(uuid.uuid4())),
            Column("fullname", String(255)),
            Column("gender", String(20)),
            Column("birthday", DateTime),
            Column("phone", String(50)),
            Column("email", String(255)),
            Column("address", Text),
            Column("data", JSONB),  # Cho full-text search
            Column("updated_at", DateTime, default=datetime.datetime.now),
        )

        # Define the guests table - có provider và account_name
        guests = Table(
            "guests",
            metadata,
            Column("id", String, primary_key=True),
            Column("provider", String(50)),  # Đã chuyển từ guest_info
            Column("account_id", String(50)),
            Column("account_name", String(100)),  # Đã chuyển từ guest_info
            Column("avatar", Text),
            Column("last_message_at", DateTime, default=datetime.datetime.now),
            Column("last_message", JSONB),
            Column("created_at", DateTime, default=datetime.datetime.now),
            Column("message_count", Integer, default=0),
            Column("sentiment", String(50), default="neutral"),
            Column("assigned_to", String(50)),
            Column("info_id", String, ForeignKey("guest_infos.id", ondelete="CASCADE")),
        )

        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(metadata.create_all)

        # Thêm dữ liệu sử dụng asyncpg
        pool = await asyncpg.create_pool(**db_params)
        async with pool.acquire() as conn:
            for customer in sample_customers:
                # Tạo unique ID cho guest_info
                guest_info_id = str(uuid.uuid4())

                # Convert string dates to datetime objects
                birthday = (
                    datetime.datetime.strptime(customer["birthday"], "%Y-%m-%d")
                    if customer["birthday"]
                    else None
                )
                last_message_at = (
                    datetime.datetime.strptime(
                        customer["last_message_at"], "%Y-%m-%d %H:%M:%S"
                    )
                    if customer["last_message_at"]
                    else None
                )

                # Tạo trường data cho full-text search (không bao gồm provider và account_name)
                data = {
                    "fullname": customer["fullname"],
                    "phone": customer["phone"],
                    "email": customer["email"],
                    "address": customer["address"],
                    "interests": [],  # Ban đầu chưa có interests
                }

                # Thêm guest_info trước - không có provider và account_name
                await conn.execute(
                    """
                INSERT INTO guest_infos (id, fullname, gender, birthday, phone, email, address, data, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    guest_info_id,
                    customer["fullname"],
                    customer["gender"],
                    birthday,
                    customer["phone"],
                    customer["email"],
                    customer["address"],
                    json.dumps(data),
                    datetime.datetime.now(),
                )

                # Sau đó thêm guest với provider và account_name ở bảng guest
                await conn.execute(
                    """
                INSERT INTO guests (id, provider, account_id, account_name, avatar, last_message_at, 
                                last_message, created_at, message_count, sentiment, assigned_to, info_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    provider = EXCLUDED.provider,
                    account_id = EXCLUDED.account_id,
                    account_name = EXCLUDED.account_name,
                    avatar = EXCLUDED.avatar,
                    last_message_at = EXCLUDED.last_message_at,
                    last_message = EXCLUDED.last_message,
                    message_count = EXCLUDED.message_count,
                    sentiment = EXCLUDED.sentiment,
                    assigned_to = EXCLUDED.assigned_to,
                    info_id = EXCLUDED.info_id
                """,
                    customer["id"],
                    # Sử dụng provider trực tiếp ở bảng guest
                    customer["provider"],
                    customer["account_id"],
                    # Sử dụng account_name trực tiếp ở bảng guest
                    customer["account_name"],
                    customer["avatar"],
                    last_message_at,
                    json.dumps({}),
                    datetime.datetime.now(),
                    customer["message_count"],
                    customer["sentiment"],
                    customer["assigned_to"],
                    guest_info_id,
                )

        print(
            f"Successfully inserted {len(sample_customers)} customers into the guests and guest_infos tables"
        )

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection pool and engine
        await engine.dispose()
        if "pool" in locals():
            await pool.close()


# Run the async function
if __name__ == "__main__":
    asyncio.run(create_and_insert_guests())
