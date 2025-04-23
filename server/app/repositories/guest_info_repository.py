from app.models import GuestInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_guest_info_by_id(db: AsyncSession, guest_info_id: str) -> GuestInfo:
    """
    Lấy guest info theo id
    """
    stmt = select(GuestInfo).where(GuestInfo.id == guest_info_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_guest_info(db: AsyncSession, guest_info: GuestInfo) -> GuestInfo:
    """
    Thêm mới guest info
    """
    db.add(guest_info)
    await db.flush()
    return guest_info


async def update_guest_info(db: AsyncSession, guest_info: GuestInfo) -> GuestInfo:
    """
    Cập nhật guest info
    """
    db.add(guest_info)
    await db.flush()
    return guest_info


async def search_guest_infos(
    db: AsyncSession, keyword: str, skip: int, limit: int
) -> list[GuestInfo]:
    """
    Tìm kiếm guest info sử dụng PGroonga full-text search
    """
    # Sử dụng PGroonga để tìm kiếm trong trường data
    stmt = f"""
    SELECT gi.*
    FROM guest_infos gi
    WHERE gi.data &@~ :keyword
    LIMIT :limit OFFSET :skip
    """
    result = await db.execute(stmt, {"keyword": keyword, "limit": limit, "skip": skip})
    return result.mappings().all()


async def count_search_result(db: AsyncSession, keyword: str) -> int:
    """
    Đếm số lượng kết quả tìm kiếm
    """
    stmt = f"""
    SELECT COUNT(*) as count
    FROM guest_infos gi
    WHERE gi.data &@~ :keyword
    """
    result = await db.execute(stmt, {"keyword": keyword})
    return result.scalar()
