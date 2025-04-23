from app.models import Guest, Interest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload


async def count_guests(db: AsyncSession) -> int:
    stmt = select(Guest)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_guests_by_assignment(db: AsyncSession, assigned_to: str) -> int:
    stmt = select(Guest).where(Guest.assigned_to == assigned_to)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_guests(db: AsyncSession, skip: int, limit: int) -> list[Guest]:
    # Eager load guest_info
    stmt = select(Guest).options(joinedload(Guest.info)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_conversation(
    db: AsyncSession, skip: int, limit: int
) -> list[Guest]:
    # Eager load guest_info
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info))
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_conversation_by_assignment(
    db: AsyncSession, assigned_to: str, skip: int, limit: int
) -> list[Guest]:
    # Eager load guest_info
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info))
        .where(Guest.assigned_to == assigned_to)
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_conversation_by_provider(
    db: AsyncSession, provider: str, account_id: str
) -> Guest:
    # Sửa lại để tìm theo provider trực tiếp từ guest thay vì từ guest_info
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info))
        .where(Guest.provider == provider, Guest.account_id == account_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_guest(db: AsyncSession, guest: Guest) -> Guest:
    db.add(guest)
    await db.flush()
    return guest


async def update_last_message(
    db: AsyncSession, guest_id: str, last_message, last_message_at
) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.last_message_at = last_message_at
        guest.last_message = last_message
        return guest
    return None


async def update_sentiment(db: AsyncSession, guest_id: str, sentiment: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.sentiment = sentiment
        return guest
    return None


async def increase_message_count(db: AsyncSession, guest_id: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.message_count += 1
        return guest
    return None


async def reset_message_count(db: AsyncSession, guest_id: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.message_count = 0
        return guest
    return None


async def count_guests_by_sentiment(db: AsyncSession, sentiment: str) -> int:
    stmt = select(Guest).where(Guest.sentiment == sentiment)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_guests_by_sentiment(
    db: AsyncSession, sentiment: str, skip: int, limit: int
) -> list[Guest]:
    # Eager load guest_info
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info))
        .where(Guest.sentiment == sentiment)
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_assignment(db: AsyncSession, guest_id: str, assigned_to: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.assigned_to = assigned_to
        return guest
    return None


async def get_guest_by_id(db: AsyncSession, guest_id: str) -> Guest:
    # Eager load cả guest_info và interests
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info), selectinload(Guest.interests))
        .where(Guest.id == guest_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_guest(db: AsyncSession, guest: Guest) -> Guest:
    db.add(guest)
    await db.flush()
    return guest


async def get_paging_guests_with_interests(
    db: AsyncSession, skip: int, limit: int
) -> list[Guest]:
    """
    Get paginated guests với interests được eagerly loaded
    """
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info), selectinload(Guest.interests))
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def add_interest_to_guest(
    db: AsyncSession, guest_id: str, interest_id: str
) -> Guest:
    """
    Thêm interest cho guest
    """
    stmt_guest = select(Guest).where(Guest.id == guest_id)
    result_guest = await db.execute(stmt_guest)
    guest = result_guest.scalars().first()

    stmt_interest = select(Interest).where(Interest.id == interest_id)
    result_interest = await db.execute(stmt_interest)
    interest = result_interest.scalars().first()

    if guest and interest:
        guest.interests.append(interest)
        await db.flush()

    return guest


async def remove_interest_from_guest(
    db: AsyncSession, guest_id: str, interest_id: str
) -> Guest:
    """
    Xóa interest khỏi guest
    """
    stmt_guest = select(Guest).where(Guest.id == guest_id)
    result_guest = await db.execute(stmt_guest)
    guest = result_guest.scalars().first()

    stmt_interest = select(Interest).where(Interest.id == interest_id)
    result_interest = await db.execute(stmt_interest)
    interest = result_interest.scalars().first()

    if guest and interest and interest in guest.interests:
        guest.interests.remove(interest)
        await db.flush()

    return guest


async def search_guests_by_keywords(
    db: AsyncSession, keywords: str, skip: int, limit: int
) -> list[Guest]:
    """
    Tìm kiếm guest sử dụng PGroonga thông qua bảng guest_info
    """
    stmt = f"""
    SELECT g.*
    FROM guests g
    JOIN guest_infos gi ON g.info_id = gi.id
    WHERE gi.data &@~ :keywords OR g.provider &@~ :keywords OR g.account_name &@~ :keywords
    ORDER BY g.last_message_at DESC
    LIMIT :limit OFFSET :skip
    """
    result = await db.execute(
        stmt, {"keywords": keywords, "limit": limit, "skip": skip}
    )
    guests_rows = result.mappings().all()

    # Chuyển đổi kết quả thành danh sách guest objects
    guests = []
    for row in guests_rows:
        # Query lại để lấy đầy đủ thông tin cho mỗi guest
        guest = await get_guest_by_id(db, row["id"])
        if guest:
            guests.append(guest)

    return guests


async def count_search_guests(db: AsyncSession, keywords: str) -> int:
    """
    Đếm số lượng kết quả tìm kiếm
    """
    stmt = f"""
    SELECT COUNT(*) as count
    FROM guests g
    JOIN guest_infos gi ON g.info_id = gi.id
    WHERE gi.data &@~ :keywords
    """
    result = await db.execute(stmt, {"keywords": keywords})
    return result.scalar()
