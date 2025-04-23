from app.configs.database import get_session
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.get("")
async def get_guests(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all guests from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    include_interests = (
        request.query_params.get("include_interests", "").lower() == "true"
    )
    keyword = request.query_params.get("keyword", None)

    filter_params = {}
    if keyword:
        filter_params["keyword"] = keyword

    if include_interests or keyword:
        guests = await guest_service.get_pagination_guests_with_interests(
            db, page, limit, filter_params
        )
    else:
        guests = await guest_service.get_pagination_guests(db, page, limit)

    return guests


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
