from datetime import datetime

from app.dtos import PaginationDto, PagingDto
from app.models import Guest, GuestInfo
from app.repositories import chat_repository, guest_info_repository, guest_repository
from sqlalchemy.ext.asyncio import AsyncSession


def process_keyword(keyword: str) -> str:
    """
    Process keyword string by splitting by comma, stripping whitespace from each part,
    and joining them back with spaces.

    Args:
        keyword: The input keyword string (e.g. "coffee, tea, water")

    Returns:
        Processed keyword string (e.g. "coffee tea water")
    """
    if not keyword:
        return ""
    parts = keyword.split(",")
    cleaned_parts = [part.strip() for part in parts]
    return " ".join(cleaned_parts)


async def get_conversations(db: AsyncSession, skip: int, limit: int) -> PagingDto:
    count = await guest_repository.count_guests(db)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_paging_conversation(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        for guest in data
    ]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_conversations_by_assignment(
    db: AsyncSession, assigned_to: str, skip: int, limit: int
) -> PagingDto:
    count = await guest_repository.count_guests_by_assignment(db, assigned_to)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_paging_conversation_by_assignment(
        db, assigned_to, skip, limit
    )
    # Convert all objects to dictionaries
    data_dict = [
        guest.to_dict(include=["info", "interests", "last_chat_message"])
        for guest in data
    ]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_chat_by_guest_id(
    db: AsyncSession, guest_id: str, skip: int, limit: int
) -> PagingDto:
    count = await chat_repository.count_chat_by_guest_id(db, guest_id)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await chat_repository.get_chat_by_guest_id(db, guest_id, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [chat.to_dict() for chat in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_conversation_by_provider(
    db: AsyncSession, provider: str, account_id: str
) -> dict:
    guest = await guest_repository.get_conversation_by_provider(
        db, provider, account_id
    )
    return (
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        if guest
        else None
    )


async def insert_guest(db: AsyncSession, guest_data: dict) -> dict:
    guest = Guest(
        provider=guest_data.get("provider"),
        account_id=guest_data.get("account_id"),
        account_name=guest_data.get("account_name"),
        avatar=guest_data.get("avatar"),
        assigned_to=guest_data.get("assigned_to", "AI"),
    )
    guest = await guest_repository.insert_guest(db, guest)
    info = guest_data.get("info")

    birthday_str = info.get("birthday")
    birthday_dt = None
    if birthday_str:
        try:
            # Attempt to parse as YYYY-MM-DD or ISO format
            if isinstance(birthday_str, str):
                dt_with_tz = datetime.fromisoformat(birthday_str.replace("Z", "+00:00"))
                birthday_dt = datetime(
                    dt_with_tz.year, dt_with_tz.month, dt_with_tz.day
                )
            elif isinstance(birthday_str, datetime):  # Already a datetime object
                birthday_dt = datetime(
                    birthday_str.year, birthday_str.month, birthday_str.day
                )
        except ValueError:
            # Handle cases where parsing might fail or if it's already a date object
            try:
                birthday_dt = datetime.strptime(birthday_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                birthday_dt = None  # Or handle error as appropriate

    guest_info = GuestInfo(
        fullname=info.get("fullname"),
        gender=info.get("gender"),
        birthday=birthday_dt,
        phone=info.get("phone"),
        email=info.get("email"),
        address=info.get("address"),
        guest_id=guest.id,
    )
    guest_info = await guest_info_repository.insert_guest_info(db, guest_info)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict()


async def update_assignment(db: AsyncSession, guest_id: str, assigned_to: str) -> dict:
    guest = await guest_repository.update_assignment(db, guest_id, assigned_to)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict(include=["interests", "info", "last_chat_message"])


async def get_guest_by_id(db: AsyncSession, guest_id: str) -> Guest:
    guest = await guest_repository.get_guest_by_id(db, guest_id)
    return (
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        if guest
        else None
    )


async def update_guest_by_id(db: AsyncSession, guest_id: str, body: dict) -> Guest:
    guest = await guest_repository.get_guest_by_id(db, guest_id)
    if not guest:
        return None  # Lấy hoặc tạo GuestInfo nếu chưa có
    if not guest.info:
        guest_info = GuestInfo(guest_id=guest.id)
        guest_info = await guest_info_repository.insert_guest_info(db, guest_info)
    else:
        guest_info = guest.info

    # Cập nhật thông tin trong GuestInfo
    guest_info.fullname = body.get("fullname", guest_info.fullname)
    guest_info.email = body.get("email", guest_info.email)
    guest_info.phone = body.get("phone", guest_info.phone)
    guest_info.address = body.get("address", guest_info.address)
    guest_info.gender = body.get("gender", guest_info.gender)

    # Xử lý định dạng birthday nếu có
    if "birthday" in body and body["birthday"]:
        try:
            # Parse datetime với timezone info
            dt_with_tz = datetime.fromisoformat(body["birthday"].replace("Z", "+00:00"))
            # Chuyển thành datetime không có timezone
            guest_info.birthday = datetime(
                dt_with_tz.year, dt_with_tz.month, dt_with_tz.day
            )
        except (ValueError, AttributeError):
            pass

    # Cập nhật GuestInfo
    await guest_info_repository.update_guest_info(db, guest_info)

    # Cập nhật interests nếu có trong body
    if "interest_ids" in body and isinstance(body["interest_ids"], list):
        # Lấy danh sách interest_ids mới
        new_interest_ids = body["interest_ids"]

        # Lấy danh sách interest_ids hiện tại
        current_interest_ids = [interest.id for interest in guest.interests]

        # Tìm interests để thêm (có trong new nhưng không có trong current)
        interests_to_add = [
            id for id in new_interest_ids if id not in current_interest_ids
        ]
        if interests_to_add:
            await guest_repository.add_interests_to_guest_by_id(
                db, guest_id, interests_to_add
            )

        # Tìm interests để xóa (có trong current nhưng không có trong new)
        interests_to_remove = [
            id for id in current_interest_ids if id not in new_interest_ids
        ]
        if interests_to_remove:
            await guest_repository.remove_interests_from_guest_by_id(
                db, guest_id, interests_to_remove
            )

    # Cập nhật Guest
    guest = await guest_repository.update_guest(db, guest)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict(include=["interests", "info", "last_chat_message"])


async def get_pagination_guests_with_interests(
    db: AsyncSession, page: int, limit: int, interest_ids: list[str]
) -> PaginationDto:
    # Lọc theo interest_ids
    count = await guest_repository.count_guests_by_interests(db, interest_ids)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await guest_repository.get_guests_by_interests(db, interest_ids, skip, limit)
    data_dict = [
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        for guest in data
    ]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_pagination_guests_with_keywords(
    db: AsyncSession, page: int, limit: int, keyword: str
) -> PaginationDto:
    count = await guest_repository.count_guests_by_keywords(db, keyword)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])

    skip = (page - 1) * limit
    data = await guest_repository.search_guests_by_keywords(db, keyword, skip, limit)
    data_dict = [
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        for guest in data
    ]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_pagination_guests_with_interests_keywords(
    db: AsyncSession, page: int, limit: int, interest_ids: list[str], keyword: str
) -> PaginationDto:
    count = await guest_repository.count_guests_by_interests_and_keywords(
        db, interest_ids, keyword
    )
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await guest_repository.get_guests_by_interests_and_keywords(
        db, interest_ids, keyword, skip, limit
    )
    data_dict = [
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        for guest in data
    ]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_pagination_guests(
    db: AsyncSession, page: int, limit: int
) -> PaginationDto:
    count = await guest_repository.count_guests(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    # Convert objects to dictionaries without including interests
    data = await guest_repository.get_paging_guests(db, skip, limit)
    data_dict = [
        guest.to_dict(include=["interests", "info", "last_chat_message"])
        for guest in data
    ]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def add_interests_to_guest(
    db: AsyncSession, guest_id: str, interest_ids: list[str]
) -> dict:
    guest = await guest_repository.add_interests_to_guest_by_id(
        db, guest_id, interest_ids
    )
    if not guest:
        return None
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict(include=["interests", "info", "last_chat_message"])


async def remove_interests_from_guest(
    db: AsyncSession, guest_id: str, interest_ids: list[str]
) -> dict:
    guest = await guest_repository.remove_interests_from_guest_by_id(
        db, guest_id, interest_ids
    )
    if not guest:
        return None
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict(include=["interests", "info", "last_chat_message"])


async def delete_guest_by_id(db: AsyncSession, guest_id: str) -> dict:
    guest = await guest_repository.delete_guest_by_id(db, guest_id)
    if not guest:
        return None
    await db.commit()
    return guest.to_dict()


async def delete_multiple_guests(db: AsyncSession, guest_ids: list[str]) -> None:
    await guest_repository.delete_multiple_guests(db, guest_ids)
    await db.commit()
