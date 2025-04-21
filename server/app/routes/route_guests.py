from app.configs.database import get_session
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/guests", tags=["Guests"])


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
