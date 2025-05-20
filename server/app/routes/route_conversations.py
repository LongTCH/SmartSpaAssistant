from app.configs.database import get_session
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("")
async def get_conversations(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all conversations from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    assigned_to = request.query_params.get("assigned_to", "all")
    if assigned_to == "all":
        conversations = await guest_service.get_conversations(db, skip, limit)
        return conversations
    conversations = await guest_service.get_conversations_by_assignment(
        db, assigned_to, skip, limit
    )
    return conversations


@router.patch("/{guest_id}/assignment")
async def update_assignment(
    guest_id: str, request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Update the assignment of a conversation.
    """
    body = await request.json()
    assigned_to = body.get("assigned_to")

    if not assigned_to:
        raise HTTPException(status_code=400, detail="assigned_to is required")

    guest = await guest_service.update_assignment(db, guest_id, assigned_to)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.get("/{guest_id}")
async def get_conversation_by_guest_id(
    request: Request, guest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get conversation by guest_id from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    conversations = await guest_service.get_chat_by_guest_id(db, guest_id, skip, limit)
    return conversations
