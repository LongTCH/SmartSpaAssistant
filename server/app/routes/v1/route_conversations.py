from typing import Optional

from app.configs.database import get_session
from app.services import guest_service
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])


class ConversationResponse(BaseModel):
    """Conversation response model"""

    id: str = Field(..., description="Unique identifier for the guest/conversation")
    name: Optional[str] = Field(None, description="Guest name")
    phone: Optional[str] = Field(None, description="Guest phone number")
    address: Optional[str] = Field(None, description="Guest address")
    assigned_to: Optional[str] = Field(
        None, description="User ID assigned to handle this conversation"
    )
    created_at: str = Field(..., description="Conversation creation timestamp")
    last_message: Optional[dict] = Field(
        None, description="Last message in the conversation"
    )

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """Chat message response model"""

    id: str = Field(..., description="Unique identifier for the message")
    guest_id: str = Field(
        ..., description="ID of the guest who sent/received the message"
    )
    sender: str = Field(..., description="Message sender (guest or system)")
    content: str = Field(..., description="Message content")
    created_at: str = Field(..., description="Message timestamp")

    class Config:
        from_attributes = True


class AssignmentUpdate(BaseModel):
    """Request model for updating conversation assignment"""

    assigned_to: str = Field(..., description="User ID to assign the conversation to")


@router.get(
    "",
    summary="Get conversations",
    description="""
    Retrieve conversations with filtering and pagination options.
    
    **Filter Options:**
    - **assigned_to=all**: Get all conversations (default)
    - **assigned_to=user_id**: Get conversations assigned to specific user
    
    **Pagination:**
    - Use skip and limit parameters for pagination
    """,
    responses={
        200: {
            "description": "List of conversations retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "skip": 0,
                        "limit": 1,
                        "data": [
                            {
                                "id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                                "provider": "web",
                                "account_id": "709685455386382",
                                "account_name": "jane71",
                                "avatar": "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/people/jazz.jpg",
                                "created_at": "2025-06-05T04:48:41.213595",
                                "assigned_to": "me",
                                "info": {
                                    "id": "a1ebf760-51fc-4435-af22-d8218ba8ce32",
                                    "fullname": "Bảo Đặng",
                                    "gender": "male",
                                    "birthday": "2000-07-09T00:00:00",
                                    "phone": "+84 25 7923564",
                                    "email": "john65@example.org",
                                    "address": "826 John Số, Quận JaneThành phố, 778730",
                                },
                                "interests": [
                                    {
                                        "id": "1b5be923-b87c-4b02-ab14-e21cb5934bb2",
                                        "name": "trẻ hóa da",
                                        "related_terms": "trẻ hóa da, làm trẻ, trẻ hóa làn da",
                                        "status": "published",
                                        "color": "#3357FF",
                                        "created_at": "2025-06-05T04:48:39.900131",
                                    }
                                ],
                                "last_chat_message": {
                                    "id": "24c2b5ef-4d8a-4741-b957-4cc673cf9e5e",
                                    "guest_id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                                    "content": {
                                        "side": "staff",
                                        "message": {
                                            "text": "Mailisa rất vui được hỗ trợ bạn. Nếu bạn có bất kỳ thắc mắc nào khác, đừng ngần ngại liên hệ với chúng tôi nhé. Chúc bạn một ngày tốt lành!"
                                        },
                                    },
                                    "created_at": "2025-06-05T01:34:42.704046",
                                },
                            }
                        ],
                        "total": 101,
                        "has_next": True,
                        "has_prev": False,
                    }
                }
            },
        }
    },
)
async def get_conversations(
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of conversations to return"
    ),
    assigned_to: str = Query(
        "all", description="Filter by assigned user ID or 'all' for all conversations"
    ),
    db: AsyncSession = Depends(get_session),
):
    """
    Get all conversations from the database with filtering and pagination.
    """
    if assigned_to == "all":
        conversations = await guest_service.get_conversations(db, skip, limit)
        return conversations.model_dump()
    conversations = await guest_service.get_conversations_by_assignment(
        db, assigned_to, skip, limit
    )
    return conversations.model_dump()


@router.patch(
    "/{guest_id}/assignment",
    summary="Update conversation assignment",
    description="""
    Assign a conversation to a specific user for handling.
    
    **Use Cases:**
    - Assign new conversations to available agents
    - Transfer conversations between agents
    - Re-assign conversations when agents are unavailable
    """,
    responses={
        200: {
            "description": "Conversation assignment updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                        "provider": "web",
                        "account_id": "709685455386382",
                        "account_name": "jane71",
                        "avatar": "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/people/jazz.jpg",
                        "created_at": "2025-06-05T04:48:41.213595",
                        "assigned_to": "user_789",
                        "info": {
                            "id": "a1ebf760-51fc-4435-af22-d8218ba8ce32",
                            "fullname": "Bảo Đặng",
                            "gender": "male",
                            "birthday": "2000-07-09T00:00:00",
                            "phone": "+84 25 7923564",
                            "email": "john65@example.org",
                            "address": "826 John Số, Quận JaneThành phố, 778730",
                        },
                        "interests": [
                            {
                                "id": "1b5be923-b87c-4b02-ab14-e21cb5934bb2",
                                "name": "trẻ hóa da",
                                "related_terms": "trẻ hóa da, làm trẻ, trẻ hóa làn da",
                                "status": "published",
                                "color": "#3357FF",
                                "created_at": "2025-06-05T04:48:39.900131",
                            }
                        ],
                        "last_chat_message": {
                            "id": "24c2b5ef-4d8a-4741-b957-4cc673cf9e5e",
                            "guest_id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                            "content": {
                                "side": "staff",
                                "message": {
                                    "text": "Conversation assigned successfully"
                                },
                            },
                            "created_at": "2025-06-05T01:34:42.704046",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Bad request - missing assigned_to",
            "content": {
                "application/json": {"example": {"detail": "assigned_to is required"}}
            },
        },
        404: {
            "description": "Guest/conversation not found",
            "content": {"application/json": {"example": {"detail": "Guest not found"}}},
        },
    },
)
async def update_assignment(
    request_body: AssignmentUpdate,
    guest_id: str = Path(..., description="ID of the guest/conversation to update"),
    db: AsyncSession = Depends(get_session),
):
    """
    Update the assignment of a conversation.
    """
    guest = await guest_service.update_assignment(
        db, guest_id, request_body.assigned_to
    )
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.get(
    "/{guest_id}",
    summary="Get conversation messages",
    description="""
    Retrieve all messages for a specific conversation/guest.
    
    **Returns:**
    - Complete chat history for the guest
    - Messages sorted by timestamp
    - Includes both guest and system messages
    
    **Pagination:**
    - Use skip and limit parameters for large conversations
    """,
    responses={
        200: {
            "description": "Conversation messages retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "skip": 0,
                        "limit": 2,
                        "data": [
                            {
                                "id": "24c2b5ef-4d8a-4741-b957-4cc673cf9e5e",
                                "guest_id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                                "content": {
                                    "side": "staff",
                                    "message": {
                                        "text": "Mailisa rất vui được hỗ trợ bạn. Nếu bạn có bất kỳ thắc mắc nào khác, đừng ngần ngại liên hệ với chúng tôi nhé. Chúc bạn một ngày tốt lành!"
                                    },
                                },
                                "created_at": "2025-06-05T01:34:42.704046",
                            },
                            {
                                "id": "a82a74eb-3a03-4d0a-bdb9-379458d86ef6",
                                "guest_id": "ebc89767-fb50-4b84-bdc3-59cd78214c09",
                                "content": {
                                    "side": "client",
                                    "message": {
                                        "text": "Dạ, cảm ơn bạn. Mình sẽ liên hệ hotline hoặc ghé chi nhánh gần nhất để được tư vấn thêm ạ."
                                    },
                                },
                                "created_at": "2025-06-05T01:34:37.704046",
                            },
                        ],
                        "total": 8,
                        "has_next": True,
                        "has_prev": False,
                    }
                }
            },
        },
        404: {
            "description": "Guest not found",
            "content": {"application/json": {"example": {"detail": "Guest not found"}}},
        },
    },
)
async def get_conversation_by_guest_id(
    guest_id: str = Path(
        ..., description="ID of the guest whose conversation to retrieve"
    ),
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of messages to return"
    ),
    db: AsyncSession = Depends(get_session),
):
    """
    Get conversation messages by guest_id from the database.
    """
    conversations = await guest_service.get_chat_by_guest_id(db, guest_id, skip, limit)
    return conversations.model_dump()
