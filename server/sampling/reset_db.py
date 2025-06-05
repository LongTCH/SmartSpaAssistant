import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncio

from app.configs.database import async_session
from app.models import Chat, Guest, GuestInfo, Interest, guest_interests
from sampling.chats import insert_chats
from sampling.guest_interests import insert_guest_interests
from sampling.guests import insert_guests
from sampling.interests import insert_interests
from sqlalchemy import delete


async def delete_all_tables_row() -> None:
    """
    Xóa tất cả các bản ghi trong cơ sở dữ liệu
    """
    async with async_session() as db:
        await db.execute(delete(Guest))
        await db.execute(delete(GuestInfo))
        await db.execute(delete(guest_interests))
        await db.execute(delete(Chat))
        await db.execute(delete(Interest))
        await db.commit()


async def reset_db() -> None:

    await delete_all_tables_row()
    await insert_interests()
    await insert_guests()
    await insert_guest_interests()
    await insert_chats()
    print("Database has been reset and sample data has been inserted.")


if __name__ == "__main__":
    asyncio.run(reset_db())
