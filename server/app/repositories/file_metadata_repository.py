from app.models import FileMetaData
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_files(db: AsyncSession, file_ids: list[str]) -> None:
    stmt = delete(FileMetaData).where(FileMetaData.id.in_(file_ids))
    await db.execute(stmt)
    # Không cần gọi db.commit() ở đây, vì giao dịch được quản lý ở cấp cao hơn


def insert_or_update_documents(db: AsyncSession, documents: list[FileMetaData]) -> None:
    db.add_all(documents)
