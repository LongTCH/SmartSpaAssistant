import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncio
import json

from app.configs.database import with_session
from app.services import guest_service

with open("sampling/customers.json", "r", encoding="utf-8") as f:
    sample_customers = json.load(f)


async def insert_guests():
    for customer in sample_customers:
        await with_session(lambda db: guest_service.insert_guest(db, customer))


if __name__ == "__main__":
    asyncio.run(insert_guests())
