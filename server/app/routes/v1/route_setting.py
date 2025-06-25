from typing import Any, Dict

from app.configs.database import get_session
from app.dtos import SettingDetailsDto, SettingUpdateDto, common_error_responses
from app.services import setting_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/settings", tags=["Settings"])


@router.get(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get local configuration data",
    description="""
    Retrieve the current local configuration data including chat settings, 
    bot identity, and behavior instructions.
    
    This endpoint returns the raw configuration dictionary as stored in the system.
    """,
    responses={
        200: {
            "description": "Local configuration data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "chat_wait_seconds": 2.5,
                        "max_script_retrieval": 10,
                        "reaction_message": "Thank you for your message!",
                        "identity": "I am a helpful assistant",
                        "instructions": "Be helpful and polite in all interactions",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_settings(db: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """Get current local configuration data."""
    try:
        return await setting_service.get_setting_details(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put(
    "",
    response_model=SettingDetailsDto,
    status_code=status.HTTP_200_OK,
    summary="Update local configuration data",
    description="""
    Update the local configuration data with new values.
    
    This endpoint accepts a dictionary of configuration updates and applies them
    to the system. Only the provided fields will be updated, others remain unchanged.
    
    **Configuration Fields:**
    - `chat_wait_seconds`: Delay between chat responses (float, >= 0)
    - `max_script_retrieval`: Maximum scripts to retrieve (integer, >= 1)
    - `reaction_message`: Default reaction message (string)
    - `identity`: Bot identity description (string)
    - `instructions`: Bot behavior instructions (string)
    """,
    responses={
        200: {
            "description": "Configuration updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "chat_wait_seconds": 3.0,
                        "max_script_retrieval": 15,
                        "reaction_message": "Thanks for reaching out!",
                        "identity": "I am your AI assistant",
                        "instructions": "Always be helpful and provide accurate information",
                    }
                }
            },
        },
        400: {
            "description": "Invalid configuration data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid value for CHAT_WAIT_SECONDS: must be >= 0"
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def update_settings(
    data: SettingUpdateDto, db: AsyncSession = Depends(get_session)
) -> SettingDetailsDto:
    """Update local configuration data."""
    try:
        # Validate numeric constraints (Pydantic already validates ge constraints, but we can add custom validation)
        if data.chat_wait_seconds is not None and data.chat_wait_seconds < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chat_wait_seconds must be >= 0",
            )

        if data.max_script_retrieval is not None and data.max_script_retrieval < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_script_retrieval must be >= 1",
            )

        # Update settings through service
        setting = await setting_service.update_settings(db, data)
        details = setting.details

        # Convert Setting object to SettingDetailsDto format
        return SettingDetailsDto(**details)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings",
        )
