from app.models import Guest, Interest, guest_interest
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import text


async def count_guests(db: AsyncSession) -> int:
    stmt = select(Guest)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_guests_by_assignment(db: AsyncSession, assigned_to: str) -> int:
    stmt = select(Guest).where(Guest.assigned_to == assigned_to)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_guests_by_interests(db: AsyncSession, interest_ids: list[str]) -> int:
    """
    Đếm số lượng khách hàng theo danh sách interest_ids
    """
    stmt = select(Guest).join(Guest.interests).where(Interest.id.in_(interest_ids))
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_guests_by_interests_and_keywords(
    db: AsyncSession, interest_ids: list[str], keywords: str
) -> int:
    """
    Đếm số lượng khách hàng theo danh sách interest_ids và từ khóa tìm kiếm
    """
    stmt = text(
        """
        SELECT COUNT(DISTINCT g.id)
        FROM guests g
        JOIN guest_infos gi ON g.info_id = gi.id
        JOIN guest_interests gi2 ON g.id = gi2.guest_id
        WHERE gi.data &@~ :keywords 
        AND gi2.interest_id = ANY(:interest_ids)
        """
    )

    result = await db.execute(
        stmt.bindparams(keywords=keywords, interest_ids=interest_ids)
    )

    count = result.scalar_one()
    return count


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
        .options(joinedload(Guest.info), selectinload(Guest.interests))
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
        .options(joinedload(Guest.info), selectinload(Guest.interests))
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
    stmt = select(Guest).options(joinedload(Guest.info)).where(Guest.id == guest_id)
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


async def search_guests_by_keywords(
    db: AsyncSession, keywords: str, skip: int, limit: int
) -> list[Guest]:
    """
    Tìm kiếm guest sử dụng PGroonga thông qua bảng guest_info
    """
    stmt = text(
        f"""
    SELECT g.*
    FROM guests g
    JOIN guest_infos gi ON g.info_id = gi.id
    WHERE gi.data &@~ :keywords
    ORDER BY g.last_message_at DESC
    LIMIT :limit OFFSET :skip
    """
    )
    result = await db.execute(
        stmt, {"limit": limit, "skip": skip, "keywords": keywords}
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

    Hỗ trợ đếm kết quả khi tìm kiếm nhiều interests cùng lúc
    """
    stmt = text(
        f"""
    SELECT COUNT(*) as count
    FROM guests g
    JOIN guest_infos gi ON g.info_id = gi.id
    WHERE gi.data &@~ :keywords
    """
    )
    result = await db.execute(stmt, {"keywords": keywords})

    return result.scalar()


async def get_guests_by_interests(
    db: AsyncSession, interest_ids: list[str], skip: int, limit: int
) -> list[Guest]:
    """
    Lấy danh sách khách hàng theo danh sách interest_ids
    """
    # Sử dụng subquery với DISTINCT để lấy unique guest IDs trước
    subquery = (
        select(Guest.id)
        .join(Guest.interests)
        .where(Interest.id.in_(interest_ids))
        .distinct()
        .order_by(Guest.id)
        .offset(skip)
        .limit(limit)
        .subquery()
    )

    # Sau đó join với subquery để lấy chi tiết guest
    stmt = (
        select(Guest)
        .options(joinedload(Guest.info), selectinload(Guest.interests))
        .join(subquery, Guest.id == subquery.c.id)
        .order_by(Guest.last_message_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_guests_by_interests_and_keywords(
    db: AsyncSession, interest_ids: list[str], keywords: str, skip: int, limit: int
) -> list[Guest]:
    """
    Lấy danh sách khách hàng theo danh sách interest_ids và từ khóa tìm kiếm
    """
    # Sử dụng text để xây dựng SQL query trực tiếp kết hợp cả tìm kiếm theo interests và keywords
    stmt = text(
        """
        SELECT DISTINCT ON (g.id) g.*
        FROM guests g
        JOIN guest_infos gi ON g.info_id = gi.id
        JOIN guest_interests gi2 ON g.id = gi2.guest_id
        WHERE gi.data &@~ :keywords 
        AND gi2.interest_id = ANY(:interest_ids)
        ORDER BY g.id, g.last_message_at DESC
        LIMIT :limit OFFSET :skip
        """
    )

    # Sử dụng bindparams để truyền parameters vào query
    result = await db.execute(
        stmt.bindparams(
            limit=limit, skip=skip, keywords=keywords, interest_ids=interest_ids
        )
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


async def delete_guest_by_id(db: AsyncSession, guest_id: str) -> Guest:
    """
    Xóa khách hàng theo ID
    """
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        await db.delete(guest)
        await db.flush()
        return guest
    return None


async def delete_multiple_guests(db: AsyncSession, guest_ids: list[str]) -> None:
    """
    Xóa nhiều khách hàng theo danh sách ID
    """
    stmt = select(Guest).where(Guest.id.in_(guest_ids))
    result = await db.execute(stmt)
    guests = result.scalars().all()
    for guest in guests:
        await db.delete(guest)
    await db.flush()


async def add_interests_to_guest_by_id(
    db: AsyncSession, guest_id: str, interest_ids: list[str]
) -> None:
    """
    Insert interest associations for a given guest using the relationship table.
    """
    from app.models import guest_interest

    for interest_id in interest_ids:
        stmt = insert(guest_interest).values(guest_id=guest_id, interest_id=interest_id)
        await db.execute(stmt)


async def remove_interests_from_guest_by_id(
    db: AsyncSession, guest_id: str, interest_ids: list[str]
) -> None:
    """
    Delete interest associations for a given guest using the relationship table.
    """
    stmt = delete(guest_interest).where(
        guest_interest.c.guest_id == guest_id,
        guest_interest.c.interest_id.in_(interest_ids),
    )
    await db.execute(stmt)
