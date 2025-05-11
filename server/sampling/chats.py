import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncio
import datetime
import json
from uuid import uuid4

from app.configs.database import async_session
from app.models import Chat
from app.repositories import guest_repository
from faker import Faker

fake = Faker()
# đọc danh sách các đoạn chat từ sampling/file_chats.json
with open("sampling/file_chats.json", "r", encoding="utf-8-sig") as f:
    sample_conversations = json.load(f)


async def insert_chats():
    async with async_session() as session:
        sample_customers = await guest_repository.get_paging_guests(session, 0, 150)
        for i, customer in enumerate(sample_customers):
            guest_id = customer.id
            last_message_at = fake.date_time_between(start_date="-1y", end_date="now")
            # Giả sử có nhiều đoạn chat khác nhau
            conversation = sample_conversations[i % len(sample_conversations)]
            conversation = list(conversation.values())[0]
            # Insert conversation for this customer
            latest_chat = None
            for t, message in enumerate(conversation):
                chat = Chat(
                    id=str(uuid4()),
                    guest_id=guest_id,
                    content=message,
                    # minus time delta 5s for each message
                    created_at=last_message_at
                    - datetime.timedelta(seconds=(len(conversation) - t - 1) * 5),
                )
                session.add(chat)
                latest_chat = chat

            customer.last_message_id = latest_chat.id

        await session.commit()


if __name__ == "__main__":
    asyncio.run(insert_chats())
