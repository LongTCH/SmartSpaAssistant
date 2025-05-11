import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncio
import json

from app.configs.database import async_session
from app.models import Interest

# Load interests from the JSON file
with open("sampling/interests.json", "r", encoding="utf-8-sig") as f:
    interests = json.load(f)


async def insert_interests():
    async with async_session() as session:
        for interest in interests:
            interest_obj = Interest(
                id=interest.get("id"),
                name=interest.get("name"),
                related_terms=interest.get("related_terms"),
                status=interest.get("status"),
                color=interest.get("color"),
            )
            session.add(interest_obj)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(insert_interests())
