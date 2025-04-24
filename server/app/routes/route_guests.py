from app.configs.database import get_session
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post("/filter")
async def filter_guests(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Tìm kiếm guests với các bộ lọc
    """
    body = await request.json()
    page = int(body.get("page", 1))
    limit = int(body.get("limit", 10))
    keyword = body.get("keyword", None)
    interest_ids = body.get("interest_ids", None)

    filter_params = {}
    if keyword:
        filter_params["keyword"] = keyword
    if interest_ids:
        filter_params["interest_ids"] = interest_ids

    guests = await guest_service.get_pagination_guests_with_interests(
        db, page, limit, filter_params
    )

    return guests


@router.post("/delete-multiple")
async def delete_multiple_guests(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple guests from the database by their IDs.
    """
    body = await request.json()
    guest_ids = body.get("guest_ids", [])
    if not guest_ids:
        raise HTTPException(status_code=400, detail="guest_ids is required")
    await guest_service.delete_multiple_guests(db, guest_ids)
    return {"message": "Guests deleted successfully"}


@router.get("/{guest_id}")
async def get_guest_by_id(
    request: Request, guest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get guest by guest_id from the database.
    """
    guest = await guest_service.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.put("/{guest_id}")
async def update_guest_by_id(
    request: Request, guest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update guest by guest_id in the database.
    """
    body = await request.json()
    guest = await guest_service.update_guest_by_id(db, guest_id, body)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.delete("/{guest_id}")
async def delete_guest_by_id(
    request: Request, guest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete guest by guest_id in the database.
    """
    guest = await guest_service.delete_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return {"message": "Guest deleted successfully"}
