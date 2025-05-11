import asyncio
import sys
from pathlib import Path

from app.configs.database import async_session
from app.models import guest_interests
from app.repositories import guest_repository, interest_repository
from faker import Faker
from sqlalchemy import insert, select

sys.path.insert(0, str(Path(__file__).parent.parent))

faker = Faker()


async def insert_guest_interests():
    async with async_session() as session:
        sample_customers = await guest_repository.get_paging_guests(session, 0, 150)
        sample_interests = await interest_repository.get_all_interests(session)
        for customer in sample_customers:
            guest_id = customer.id

            # Chọn ngẫu nhiên 1-3 interests cho mỗi guest
            num_interests = faker.random_int(min=1, max=min(3, len(sample_interests)))
            selected_interests = faker.random_elements(
                elements=sample_interests, length=num_interests, unique=True
            )

            for interest in selected_interests:
                interest_id = interest.id

                stmt = select(guest_interests).where(
                    guest_interests.c.guest_id == guest_id,
                    guest_interests.c.interest_id == interest_id,
                )
                result = await session.execute(stmt)
                relation_exists = result.scalar()

                if not relation_exists:
                    stmt = insert(guest_interests).values(
                        guest_id=guest_id,
                        interest_id=interest_id,
                    )
                    await session.execute(stmt)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(insert_guest_interests())
