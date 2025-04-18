import asyncio
import datetime

# Load sample customers from the JSON file
import uuid

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection parameters
db_params = {
    "database": "smartspa",
    "user": "root",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}

scripts = [
    {
        "id": str(uuid.uuid4()),
        "name": "CTKM/ SALE / GIẢM GIÁ/ ƯU ĐÃI/ CHIẾT KHẤU/ TRI ÂN/ DEAL",
        "description": "Khách hỏi về chương trình khuyến mãi, giảm giá, ưu đãi",
        "status": "published",
        "solution": "Hiện tại chúng tôi đang có chương trình giảm 20% cho khách hàng mới",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "CƠ SỞ / ĐỊA CHỈ / CHI NHÁNH / THỜI GIAN HOẠT ĐỘNG / MẤY GIỜ MỞ - ĐÓNG CỬA",
        "description": "Khách hỏi về địa chỉ chi nhánh, thời gian hoạt động",
        "status": "draft",
        "solution": "Chi nhánh của chúng tôi mở cửa từ 8h-22h hàng ngày, trừ ngày lễ",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "KHÁCH KHÔNG MUỐN TƯ VẤN QUA ĐIỆN THOẠI",
        "description": "Khách hàng từ chối tư vấn qua điện thoại",
        "status": "published",
        "solution": "Vâng, quý khách có thể liên hệ với chúng tôi qua tin nhắn hoặc email",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "ORDER / CHỐT ĐƠN",
        "description": "Khách hàng muốn đặt hàng, chốt đơn",
        "status": "published",
        "solution": "Để đặt hàng, quý khách vui lòng cho biết sản phẩm cần mua và địa chỉ giao hàng",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "THẺ THÀNH VIÊN / TÍCH ĐIỂM",
        "description": "Khách hỏi về thẻ thành viên, tích điểm",
        "status": "published",
        "solution": "Hệ thống tích điểm của chúng tôi: cứ 100,000đ sẽ tích 1 điểm, 10 điểm đổi voucher 50,000đ",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "DỊCH VỤ SPA / MASSAGE",
        "description": "Khách hỏi về các dịch vụ spa, massage",
        "status": "published",
        "solution": "Chúng tôi cung cấp nhiều dịch vụ spa như massage body, facial, và trị liệu",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "CHẤT LƯỢNG SẢN PHẨM / THƯƠNG HIỆU",
        "description": "Khách hỏi về chất lượng và thương hiệu sản phẩm",
        "status": "published",
        "solution": "Sản phẩm của chúng tôi đều là hàng chính hãng, có giấy chứng nhận và được kiểm định chất lượng",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "BẢO HÀNH / ĐỔI TRẢ",
        "description": "Khách hỏi về chính sách bảo hành, đổi trả",
        "status": "published",
        "solution": "Chính sách bảo hành của chúng tôi là 30 ngày đổi trả nếu có lỗi từ nhà sản xuất",
    },
]


async def create_and_insert_scripts():
    # Create a connection pool
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Define the scripts table
    metadata = MetaData()
    scripts_table = Table(
        "scripts",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("description", Text, nullable=False),
        Column("solution", Text, nullable=False),
        Column("status", String(50), default="published"),
        Column("created_at", DateTime, default=datetime.datetime.now),
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async with async_session() as session:
        for script in scripts:
            query = scripts_table.insert().values(**script)
            await session.execute(query)
        await session.commit()

    await engine.dispose()
    await session.close()


if __name__ == "__main__":
    asyncio.run(create_and_insert_scripts())
    print("Scripts inserted successfully.")
