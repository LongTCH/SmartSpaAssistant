from typing import Any, Dict

from app.dtos import common_error_responses
from app.services import setting_service
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/v2/settings", tags=["Settings"])


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
                        "CHAT_WAIT_SECONDS": 2.5,
                        "MAX_SCRIPT_RETRIEVAL": 10,
                        "REACTION_MESSAGE": "Thank you for your message!",
                        "IDENTITY": "I am a helpful assistant",
                        "INSTRUCTIONS": "Be helpful and polite in all interactions",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_local_data() -> Dict[str, Any]:
    """Get current local configuration data."""
    try:
        return await setting_service.get_local_data_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve local data: {str(e)}",
        )


# @router.put(
#     "",
#     response_model=LocalDataDto,
#     status_code=status.HTTP_200_OK,
#     summary="Update local configuration data",
#     description="""
#     Update the local configuration data with new values.

#     This endpoint accepts a dictionary of configuration updates and applies them
#     to the system. Only the provided fields will be updated, others remain unchanged.

#     **Configuration Fields:**
#     - `CHAT_WAIT_SECONDS`: Delay between chat responses (float, >= 0)
#     - `MAX_SCRIPT_RETRIEVAL`: Maximum scripts to retrieve (integer, >= 1)
#     - `REACTION_MESSAGE`: Default reaction message (string)
#     - `IDENTITY`: Bot identity description (string)
#     - `INSTRUCTIONS`: Bot behavior instructions (string)
#     """,
#     responses={
#         200: {
#             "description": "Configuration updated successfully",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "chat_wait_seconds": 3.0,
#                         "max_script_retrieval": 15,
#                         "reaction_message": "Thanks for reaching out!",
#                         "identity": "I am your AI assistant",
#                         "instructions": "Always be helpful and provide accurate information",
#                     }
#                 }
#             },
#         },
#         400: {
#             "description": "Invalid configuration data",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "detail": "Invalid value for CHAT_WAIT_SECONDS: must be >= 0"
#                     }
#                 }
#             },
#         },
#         **common_error_responses,
#     },
# )
# async def update_local_data(data: LocalDataUpdateDto) -> LocalDataDto:
#     """Update local configuration data."""
#     try:
#         # Convert Pydantic model to dict, excluding None values
#         update_dict = data.model_dump(exclude_none=True)

#         if not update_dict:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No valid configuration fields provided",
#             )

#         # Validate numeric constraints
#         if "CHAT_WAIT_SECONDS" in update_dict and update_dict["CHAT_WAIT_SECONDS"] < 0:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="CHAT_WAIT_SECONDS must be >= 0",
#             )

#         if (
#             "MAX_SCRIPT_RETRIEVAL" in update_dict
#             and update_dict["MAX_SCRIPT_RETRIEVAL"] < 1
#         ):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="MAX_SCRIPT_RETRIEVAL must be >= 1",
#             )

#         updated_data = await setting_service.save_local_data(update_dict)

#         # Convert LocalData object to LocalDataDto format
#         return LocalDataDto(
#             chat_wait_seconds=updated_data.chat_wait_seconds,
#             max_script_retrieval=updated_data.max_script_retrieval,
#             reaction_message=updated_data.reaction_message,
#             identity=updated_data.identity,
#             instructions=updated_data.instructions,
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update local data: {str(e)}",
#         )
