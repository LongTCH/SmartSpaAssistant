import asyncio
import json

from faker import Faker
from sqlalchemy import Column, ForeignKey, MetaData, String, Table, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# đọc danh sách customer từ sampling/customers.json
with open("sampling/customers.json", "r", encoding="utf-8") as f:
    sample_customers = json.load(f)

with open("sampling/interests.json", "r", encoding="utf-8-sig") as f:
    sample_interests = json.load(f)

db_params = {
    "database": "smartspa",
    "user": "root",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}


async def create_and_insert_guest_interests():
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    metadata = MetaData()

    # Định nghĩa bảng guests (chỉ cần các trường cần thiết cho khóa ngoại)
    guests = Table(
        "guests",
        metadata,
        Column("id", String, primary_key=True),
        Column("info_id", String),
        # Không cần thêm các trường khác vì chúng ta chỉ cần cấu trúc khóa
    )

    # Định nghĩa bảng interests (chỉ cần các trường cần thiết cho khóa ngoại)
    interests = Table(
        "interests",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String),
        # Không cần thêm các trường khác
    )

    # Sửa tên bảng thành guest_interests (số nhiều) để đúng với quy ước đặt tên
    guest_interests = Table(
        "guest_interests",
        metadata,
        Column(
            "guest_id",
            String,
            ForeignKey("guests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column(
            "interest_id",
            String,
            ForeignKey("interests.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    # Kiểm tra và tạo bảng nếu chưa tồn tại (sử dụng session mới để tránh xung đột transaction)
    async with AsyncSession(engine) as check_session:
        # Kiểm tra xem bảng guest_interests đã tồn tại chưa
        check_query = text(
            """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'guest_interests'
        )
        """
        )
        result = await check_session.execute(check_query)
        table_exists = result.scalar()

        if not table_exists:
            # Tạo bảng guest_interests nếu nó chưa tồn tại
            create_table_query = text(
                """
            CREATE TABLE IF NOT EXISTS guest_interests (
                guest_id VARCHAR NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
                interest_id VARCHAR NOT NULL REFERENCES interests(id) ON DELETE CASCADE
            )
            """
            )
            await check_session.execute(create_table_query)
            await check_session.commit()
            print("Đã tạo bảng guest_interests mới")

    async with async_session() as session:
        faker = Faker()
        # Với mỗi guest, gán ngẫu nhiên 1-3 interests
        for customer in sample_customers:
            guest_id = customer["id"]

            # Chọn ngẫu nhiên 1-3 interests cho mỗi guest
            num_interests = faker.random_int(min=1, max=3)
            selected_interests = faker.random_elements(
                elements=sample_interests, length=num_interests, unique=True
            )

            for interest in selected_interests:
                interest_id = interest["id"]

                # Kiểm tra xem quan hệ đã tồn tại chưa
                check_query = text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM guest_interests 
                    WHERE guest_id = :guest_id AND interest_id = :interest_id
                )
                """
                )
                result = await session.execute(
                    check_query, {"guest_id": guest_id, "interest_id": interest_id}
                )
                relation_exists = result.scalar()

                if not relation_exists:
                    # Thêm quan hệ nếu chưa tồn tại
                    insert_query = text(
                        """
                    INSERT INTO guest_interests (guest_id, interest_id) 
                    VALUES (:guest_id, :interest_id)
                    """
                    )
                    await session.execute(
                        insert_query, {"guest_id": guest_id, "interest_id": interest_id}
                    )

        await session.commit()

    await engine.dispose()
    print("Guest interests created and inserted successfully.")


if __name__ == "__main__":
    asyncio.run(create_and_insert_guest_interests())
