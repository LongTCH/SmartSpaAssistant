from app.configs.database import get_session
from app.dtos import (
    ErrorDetail,
    GuestDeleteMultipleRequest,
    GuestDeleteMultipleResponse,
    GuestDeleteResponse,
    GuestFilterRequest,
    GuestUpdate,
    common_error_responses,
)
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post(
    "/filter",
    summary="Filter guests with pagination",
    description="Search and filter guests with various criteria including keywords and interests.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved filtered guests",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "67b04bcb64e8b3ee69c17a4b",
                                "fullname": "Nguyễn Văn An",
                                "gender": "Nam",
                                "birthday": "1990-01-15",
                                "phone": "0901234567",
                                "email": "nguyenvanan@email.com",
                                "address": "123 Phố Huế, Hoàn Kiếm, Hà Nội",
                                "interest_ids": ["67b04b5c64e8b3ee69c17a32"],
                                "created_by": "system",
                                "created_at": "2024-01-15T10:30:00.000000",
                                "updated_at": "2024-01-15T10:30:00.000000",
                            },
                            {
                                "id": "67b04bcb64e8b3ee69c17a4c",
                                "fullname": "Trần Thị Bình",
                                "gender": "Nữ",
                                "birthday": "1992-05-20",
                                "phone": "0912345678",
                                "email": "tranthib@email.com",
                                "address": "456 Đường Láng, Đống Đa, Hà Nội",
                                "interest_ids": [
                                    "67b04b5c64e8b3ee69c17a33",
                                    "67b04b5c64e8b3ee69c17a34",
                                ],
                                "created_by": "admin",
                                "created_at": "2024-01-20T14:15:00.000000",
                                "updated_at": "2024-01-20T14:15:00.000000",
                            },
                        ],
                        "page": 1,
                        "limit": 10,
                        "total": 25,
                        "has_next": True,
                        "has_prev": False,
                        "next_page": 2,
                        "prev_page": None,
                        "total_pages": 3,
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def filter_guests(
    filter_data: GuestFilterRequest, db: AsyncSession = Depends(get_session)
):
    """
    Tìm kiếm guests với các bộ lọc
    """
    page = filter_data.page
    limit = filter_data.limit
    keyword = filter_data.keyword
    interest_ids = filter_data.interest_ids

    guests = []
    if keyword and interest_ids:
        guests = await guest_service.get_pagination_guests_with_interests_keywords(
            db, page, limit, interest_ids, keyword
        )
    elif keyword:
        guests = await guest_service.get_pagination_guests_with_keywords(
            db, page, limit, keyword
        )
    elif interest_ids:
        guests = await guest_service.get_pagination_guests_with_interests(
            db, page, limit, interest_ids
        )
    else:
        guests = await guest_service.get_pagination_guests(db, page, limit)

    return guests


@router.post(
    "/delete-multiple",
    summary="Delete multiple guests",
    description="Deletes multiple guests from the database by their IDs.",
    responses={
        status.HTTP_200_OK: {
            "description": "Guests deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Guests deleted successfully"}
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorDetail,
            "description": "guest_ids is required",
            "content": {
                "application/json": {"example": {"detail": "guest_ids is required"}}
            },
        },
        **common_error_responses,
    },
)
async def delete_multiple_guests(
    request_data: GuestDeleteMultipleRequest, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple guests from the database by their IDs.
    """
    guest_ids = request_data.guest_ids
    if not guest_ids:
        raise HTTPException(status_code=400, detail="guest_ids is required")
    await guest_service.delete_multiple_guests(db, guest_ids)
    return GuestDeleteMultipleResponse(message="Guests deleted successfully")


@router.get(
    "/{guest_id}",
    summary="Get guest by ID",
    description="Retrieves a specific guest by their ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved guest",
            "content": {
                "application/json": {
                    "example": {
                        "id": "67b04bcb64e8b3ee69c17a4b",
                        "fullname": "Nguyễn Văn An",
                        "gender": "Nam",
                        "birthday": "1990-01-15",
                        "phone": "0901234567",
                        "email": "nguyenvanan@email.com",
                        "address": "123 Phố Huế, Hoàn Kiếm, Hà Nội",
                        "interest_ids": ["67b04b5c64e8b3ee69c17a32"],
                        "created_by": "system",
                        "created_at": "2024-01-15T10:30:00.000000",
                        "updated_at": "2024-01-15T10:30:00.000000",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_guest_by_id(guest_id: str, db: AsyncSession = Depends(get_session)):
    """
    Get guest by guest_id from the database.
    """
    guest = await guest_service.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.put(
    "/{guest_id}",
    summary="Update an existing guest",
    description="Updates an existing guest by their ID. Only provided fields will be updated.",
    responses={
        status.HTTP_200_OK: {
            "description": "Guest updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "67b04bcb64e8b3ee69c17a4b",
                        "fullname": "Nguyễn Văn An (Đã cập nhật)",
                        "gender": "Nam",
                        "birthday": "1990-01-15",
                        "phone": "0901234567",
                        "email": "nguyenvanan.updated@email.com",
                        "address": "456 Phố Cổ, Hoàn Kiếm, Hà Nội",
                        "interest_ids": [
                            "67b04b5c64e8b3ee69c17a32",
                            "67b04b5c64e8b3ee69c17a33",
                        ],
                        "created_by": "system",
                        "created_at": "2024-01-15T10:30:00.000000",
                        "updated_at": "2024-01-15T16:45:00.000000",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def update_guest_by_id(
    guest_id: str, guest_data: GuestUpdate, db: AsyncSession = Depends(get_session)
):
    """
    Update guest by guest_id in the database.
    """
    guest = await guest_service.update_guest_by_id(
        db, guest_id, guest_data.model_dump(exclude_unset=True)
    )
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.delete(
    "/{guest_id}",
    summary="Delete a guest",
    description="Deletes a guest from the database by their ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Guest deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Guest deleted successfully"}
                }
            },
        },
        **common_error_responses,
    },
)
async def delete_guest_by_id(guest_id: str, db: AsyncSession = Depends(get_session)):
    """
    Delete guest by guest_id in the database.
    """
    guest = await guest_service.delete_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return GuestDeleteResponse(message="Guest deleted successfully")
