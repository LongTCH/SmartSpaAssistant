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
    data_dict = [guest.to_dict(include=["interests"]) for guest in data]
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
    data_dict = [guest.to_dict(include=["interests"]) for guest in data]
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
    return guest.to_dict() if guest else None


async def insert_guest(db: AsyncSession, guest_data: dict) -> dict:
    # Tạo GuestInfo không có provider và account_name
    guest_info = GuestInfo(
        fullname=guest_data.get("fullname"),
        gender=guest_data.get("gender"),
        birthday=guest_data.get("birthday"),
        phone=guest_data.get("phone"),
        email=guest_data.get("email"),
        address=guest_data.get("address"),
    )
    guest_info = await guest_info_repository.insert_guest_info(db, guest_info)

    # Tạo Guest với provider và account_name
    guest = Guest(
        provider=guest_data.get("provider"),
        account_id=guest_data.get("account_id"),
        account_name=guest_data.get("account_name"),
        avatar=guest_data.get("avatar"),
        last_message_at=guest_data.get("last_message_at"),
        last_message=guest_data.get("last_message", {}),
        message_count=guest_data.get("message_count", 0),
        sentiment=guest_data.get("sentiment", "neutral"),
        assigned_to=guest_data.get("assigned_to", "AI"),
        info_id=guest_info.id,
    )
    guest = await guest_repository.insert_guest(db, guest)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict()


async def get_paging_guests_by_sentiment(
    db: AsyncSession, sentiment: str, skip: int, limit: int
) -> PagingDto:
    count = await guest_repository.count_guests_by_sentiment(db, sentiment)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_guests_by_sentiment(db, sentiment, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [guest.to_dict() for guest in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def update_assignment(db: AsyncSession, guest_id: str, assigned_to: str) -> dict:
    guest = await guest_repository.update_assignment(db, guest_id, assigned_to)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict()


async def get_guest_by_id(db: AsyncSession, guest_id: str) -> Guest:
    guest = await guest_repository.get_guest_by_id(db, guest_id)
    return guest.to_dict(include=["interests"]) if guest else None


async def update_guest_by_id(db: AsyncSession, guest_id: str, body: dict) -> Guest:
    guest = await guest_repository.get_guest_by_id(db, guest_id)
    if not guest:
        return None

    # Lấy hoặc tạo GuestInfo nếu chưa có
    if not guest.info:
        guest_info = GuestInfo()
        guest_info = await guest_info_repository.insert_guest_info(db, guest_info)
        guest.info_id = guest_info.id
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
    return guest.to_dict(include=["interests"])


async def get_pagination_guests_with_interests(
    db: AsyncSession, page: int, limit: int, filter_params=None
) -> PaginationDto:
    if (
        filter_params
        and filter_params.get("keyword")
        and filter_params.get("interest_ids")
    ):
        # Lọc theo interest_ids và keyword
        interest_ids = filter_params.get("interest_ids")
        keyword = process_keyword(filter_params.get("keyword"))
        count = await guest_repository.count_guests_by_interests_and_keywords(
            db, interest_ids, keyword
        )
        if count == 0:
            return PaginationDto(page=page, limit=limit, total=0, data=[])
        skip = (page - 1) * limit
        data = await guest_repository.get_guests_by_interests_and_keywords(
            db, interest_ids, keyword, skip, limit
        )
        data_dict = [guest.to_dict(include=["interests"]) for guest in data]
        return PaginationDto(page=page, limit=limit, total=count, data=data_dict)
    elif filter_params and filter_params.get("keyword"):
        # Sử dụng full-text search với PGroonga
        keyword = process_keyword(filter_params.get("keyword"))
        count = await guest_repository.count_search_guests(db, keyword)
        if count == 0:
            return PaginationDto(page=page, limit=limit, total=0, data=[])

        skip = (page - 1) * limit
        data = await guest_repository.search_guests_by_keywords(
            db, keyword, skip, limit
        )
        data_dict = [guest.to_dict(include=["interests"]) for guest in data]
        return PaginationDto(page=page, limit=limit, total=count, data=data_dict)
    elif filter_params and filter_params.get("interest_ids"):
        # Lọc theo interest_ids
        interest_ids = filter_params.get("interest_ids")
        count = await guest_repository.count_guests_by_interests(db, interest_ids)
        if count == 0:
            return PaginationDto(page=page, limit=limit, total=0, data=[])
        skip = (page - 1) * limit
        data = await guest_repository.get_guests_by_interests(
            db, interest_ids, skip, limit
        )
        data_dict = [guest.to_dict(include=["interests"]) for guest in data]
        return PaginationDto(page=page, limit=limit, total=count, data=data_dict)
    else:
        # Phân trang bình thường
        count = await guest_repository.count_guests(db)
        if count == 0:
            return PaginationDto(page=page, limit=limit, total=0, data=[])
        skip = (page - 1) * limit
        data = await guest_repository.get_paging_guests_with_interests(db, skip, limit)
        data_dict = [guest.to_dict(include=["interests"]) for guest in data]
        return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_pagination_guests(
    db: AsyncSession, page: int, limit: int
) -> PaginationDto:
    count = await guest_repository.count_guests(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await guest_repository.get_paging_guests(db, skip, limit)
    # Convert objects to dictionaries without including interests
    data_dict = [guest.to_dict() for guest in data]
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
    return guest.to_dict(include=["interests"])


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
    return guest.to_dict(include=["interests"])


async def delete_guest_by_id(db: AsyncSession, guest_id: str) -> dict:
    guest = await guest_repository.delete_guest_by_id(db, guest_id)
    if not guest:
        return None
    await db.commit()
    return guest.to_dict()


async def delete_multiple_guests(db: AsyncSession, guest_ids: list[str]) -> None:
    await guest_repository.delete_multiple_guests(db, guest_ids)
    await db.commit()
