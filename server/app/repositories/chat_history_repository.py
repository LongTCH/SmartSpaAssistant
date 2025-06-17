from app.models import ChatHistory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_latest_history_count(db: AsyncSession, guest_id: str) -> int:
    """Lấy history_count gần nhất của guest"""
    stmt = (
        select(ChatHistory.history_count)
        .where(ChatHistory.guest_id == guest_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    count = result.scalar()
    return count or 0


async def insert_chat_history(
    db: AsyncSession, guest_id: str, content: str, summary: str, script_ids: str
) -> ChatHistory:
    # Lấy history_count hiện tại và tăng lên 1
    latest_count = await get_latest_history_count(db, guest_id)
    new_count = latest_count + 1

    chat_history = ChatHistory(
        guest_id=guest_id,
        content=content,
        summary=summary,
        used_scripts=script_ids,
        history_count=new_count,
    )
    db.add(chat_history)
    await db.flush()
    return chat_history


async def get_latest_chat_histories(
    db: AsyncSession, guest_id: str, limit: int = 5
) -> list[ChatHistory]:
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.guest_id == guest_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_long_term_memory(
    db: AsyncSession, guest_id: str, skip: int, limit=50
) -> list[str]:
    # Lấy các summary khác rỗng, sắp xếp theo thời gian tạo giảm dần
    stmt = (
        select(ChatHistory.summary)
        .where(ChatHistory.guest_id == guest_id)
        .where(ChatHistory.summary != "")  # Chỉ lấy summary khác rỗng
        .order_by(ChatHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_last_n_messages_content(
    db: AsyncSession, guest_id: str, n: int
) -> list[bytes]:
    """Lấy content của n messages cuối cùng của guest."""
    stmt = (
        select(ChatHistory.content)
        .where(ChatHistory.guest_id == guest_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(n)
    )
    result = await db.execute(stmt)
    # Trả về danh sách các content, đảo ngược để có thứ tự từ cũ nhất đến mới nhất trong n tin nhắn
    return list(reversed(result.scalars().all()))


async def insert_chat_history_without_summary(
    db: AsyncSession, guest_id: str, content: bytes, script_ids: str
) -> ChatHistory:
    """Chèn chat history mới mà không có summary, history_count tự động tăng."""
    latest_count = await get_latest_history_count(db, guest_id)
    new_count = latest_count + 1

    chat_history = ChatHistory(
        guest_id=guest_id,
        content=content,
        summary="",  # Summary rỗng
        used_scripts=script_ids,
        history_count=new_count,
    )
    db.add(chat_history)
    await db.flush()
    return chat_history
