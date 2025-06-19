from typing import Optional

from app.configs.database import get_session
from app.dtos import ErrorDetail, common_error_responses
from app.services import notification_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v2/notifications", tags=["Notifications"])

ALLOWED_PARAM_TYPES = ["String", "Integer", "Numeric", "Boolean", "DateTime"]


@router.get(
    "",
    summary="Get notifications with pagination",
    description="Retrieves a paginated list of notifications. Can be filtered by status.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved notifications",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "limit": 10,
                        "total": 15,
                        "data": [
                            {
                                "id": "notification-123",
                                "title": "Thông báo mới",
                                "message": "Đây là nội dung thông báo mới",
                                "status": "published",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T12:30:00Z",
                            }
                        ],
                        "has_next": True,
                        "has_prev": False,
                        "next_page": 2,
                        "prev_page": None,
                        "total_pages": 2,
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_notifications(
    db: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status_filter: Optional[str] = Query(
        "all",
        alias="status",
        description="Filter notifications by status ('published', 'draft', or 'all')",
    ),
):
    """
    Get all notifications from the database with pagination and status filtering.
    """
    if status_filter == "all":
        notifications = await notification_service.get_notifications(db, page, limit)
    else:
        notifications = await notification_service.get_notifications_by_status(
            db, page, limit, status_filter
        )
    return notifications


# @router.get(
#     "/download-template",
#     summary="Download notification template",
#     description="Downloads an Excel template file for notifications.",
#     response_class=StreamingResponse,
#     responses={
#         status.HTTP_200_OK: {
#             "description": "Excel template file for notifications.",
#             "content": {
#                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
#                     "schema": {"type": "string", "format": "binary"}
#                 }
#             },
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "model": ErrorDetail,
#             "description": "Template not found",
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "model": ErrorDetail,
#             "description": "Error generating notification template",
#         },
#     },
# )
# async def get_notification_template(db: AsyncSession = Depends(get_session)):
#     """
#     Download an Excel template file for notifications.
#     """
#     try:
#         # Get the template file path
#         excel_buffer = await notification_service.get_notification_template()
#         if not excel_buffer:
#             raise HTTPException(status_code=404, detail="Template not found")
#         response_buffer = BytesIO(excel_buffer.getvalue())
#         # Encode the filename to handle non-ASCII characters
#         filename = "Template cài đặt thông báo.xlsx"
#         encoded_filename = quote(filename)

#         # Return as streaming response with proper headers for Vietnamese filename
#         return StreamingResponse(
#             response_buffer,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             headers={
#                 "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
#                 "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
#             },
#         )
#     except Exception as e:
#         print(f"Error generating notification template: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Error generating notification template"
#         )


# @router.get(
#     "/download",
#     summary="Download all notifications as Excel",
#     description="Downloads all notifications from the database as an Excel file.",
#     response_class=StreamingResponse,
#     responses={
#         status.HTTP_200_OK: {
#             "description": "Excel file with notifications.",
#             "content": {
#                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
#                     "schema": {"type": "string", "format": "binary"}
#                 }
#             },
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "model": ErrorDetail,
#             "description": "No notifications found",
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "model": ErrorDetail,
#             "description": "Error downloading notifications",
#         },
#     },
# )
# async def download_notifications_as_excel(
#     db: AsyncSession = Depends(get_session),
# ):
#     """
#     Download all notifications as Excel file.
#     """
#     try:
#         # Get the file path from the service
#         excel_buffer = await notification_service.download_notifications_as_excel(db)
#         if not excel_buffer:
#             raise HTTPException(status_code=404, detail="No notifications found")

#         # Encode the filename to handle non-ASCII characters
#         filename = "Cài đặt thông báo.xlsx"
#         encoded_filename = quote(filename)
#         response_buffer = BytesIO(excel_buffer.getvalue())
#         # Return as streaming response with proper headers for Vietnamese filename
#         return StreamingResponse(
#             response_buffer,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             headers={
#                 "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
#                 "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
#             },
#         )
#     except Exception as e:
#         print(f"Error downloading notifications: {e}")
#         raise HTTPException(status_code=500, detail=f"Error downloading notifications")


@router.get(
    "/{id}",
    summary="Get notification by ID",
    description="Retrieves a specific notification by its ID.",
    responses={
        status.HTTP_200_OK: {"description": "Successfully retrieved notification"},
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorDetail,
            "description": "Notification not found",
        },
        **common_error_responses,
    },
)
async def get_notification_by_id(id: str, db: AsyncSession = Depends(get_session)):
    """
    Get a notification by its ID from the database.
    """
    notification = await notification_service.get_notification_by_id(db, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


# @router.post(
#     "",
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new notification",
#     description="Creates a new notification record in the database.",
#     responses={
#         status.HTTP_201_CREATED: {"description": "Successfully created notification"},
#         status.HTTP_400_BAD_REQUEST: {
#             "model": ErrorDetail,
#             "description": "Invalid notification data",
#         },
#         **common_error_responses,
#     },
# )
# async def insert_notification(
#     notification_data: NotificationCreate, db: AsyncSession = Depends(get_session)
# ):
#     """
#     Insert a new notification into the database.
#     """
#     errors = validate_notification_data(notification_data.model_dump())
#     if errors:
#         raise HTTPException(status_code=400, detail=errors)
#     await notification_service.insert_notification(db, notification_data.model_dump())
#     return NotificationCreateSuccessResponse(
#         message="Notification created successfully",
#         detail="The new notification has been added to the database.",
#     )


# @router.put(
#     "/{id}",
#     status_code=status.HTTP_204_NO_CONTENT,
#     summary="Update a notification",
#     description="Updates an existing notification by its ID.",
#     responses={
#         status.HTTP_204_NO_CONTENT: {
#             "description": "Successfully updated notification"
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "model": ErrorDetail,
#             "description": "Notification not found",
#         },
#         status.HTTP_400_BAD_REQUEST: {
#             "model": ErrorDetail,
#             "description": "Invalid notification data",
#         },
#         **common_error_responses,
#     },
# )
# async def update_notification(
#     id: str,
#     notification_data: NotificationUpdate,
#     db: AsyncSession = Depends(get_session),
# ):
#     """
#     Update a notification in the database.
#     """
#     await notification_service.update_notification(
#         db, id, notification_data.model_dump(exclude_unset=True)
#     )
#     return HttpResponse(status_code=204)


# @router.delete(
#     "/{id}",
#     summary="Delete a notification",
#     description="Deletes a specific notification by its ID.",
#     responses={
#         status.HTTP_200_OK: {"description": "Successfully deleted notification"},
#         status.HTTP_404_NOT_FOUND: {
#             "model": ErrorDetail,
#             "description": "Notification not found",
#         },
#         **common_error_responses,
#     },
# )
# async def delete_notification(id: str, db: AsyncSession = Depends(get_session)):
#     """
#     Delete a notification from the database by its ID.
#     """
#     await notification_service.delete_notification(db, id)
#     return NotificationDeleteResponse(
#         message="Notification deleted successfully",
#         detail=f"Notification with ID {id} has been removed from the database.",
#     )


# @router.post(
#     "/delete-multiple",
#     summary="Delete multiple notifications",
#     description="Deletes multiple notifications from the database by their IDs.",
#     responses={
#         status.HTTP_200_OK: {"description": "Successfully deleted notifications"},
#         status.HTTP_400_BAD_REQUEST: {
#             "model": ErrorDetail,
#             "description": "Invalid request data",
#         },
#         **common_error_responses,
#     },
# )
# async def delete_multiple_notifications(
#     delete_request: NotificationDeleteMultipleRequest,
#     db: AsyncSession = Depends(get_session),
# ):
#     """
#     Delete multiple notifications from the database by their IDs.
#     """
#     if not delete_request.notification_ids:
#         raise HTTPException(status_code=400, detail="notification_ids is required")

#     await notification_service.delete_multiple_notifications(
#         db, delete_request.notification_ids
#     )
#     return NotificationDeleteMultipleResponse(
#         message="Notifications deleted successfully",
#         detail=f"Successfully deleted {len(delete_request.notification_ids)} notifications from the database.",
#         deleted_count=len(delete_request.notification_ids),
#     )


# @router.post(
#     "/upload",
#     summary="Upload notifications from Excel file",
#     description="Uploads an Excel file containing notification data and creates new notifications in the database. The Excel file should have a 'data' sheet with notifications and individual 'n_{id}' sheets for parameters.",
#     responses={
#         status.HTTP_201_CREATED: {
#             "description": "Successfully uploaded and created notifications"
#         },
#         status.HTTP_400_BAD_REQUEST: {
#             "model": ErrorDetail,
#             "description": "Invalid file type or missing file",
#         },
#         **common_error_responses,
#     },
# )
# async def upload_notifications_excel(
#     file: UploadFile = File(..., description="Excel file containing notification data"),
#     db: AsyncSession = Depends(get_session),
# ):
#     """
#     Upload notifications from Excel file.
#     The Excel file should have:
#     1. 'data' sheet: Contains notifications with id, label, color, status, description, content
#     2. 'n_{id}' sheets: One sheet per notification with its parameters

#     Returns:
#         Success message
#     """
#     try:
#         # Validate file is an Excel file
#         content_type = file.content_type
#         if content_type not in [
#             "application/vnd.ms-excel",
#             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         ]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid file type. Only Excel files are supported.",
#             )

#         # Read file contents
#         file_contents = await file.read()

#         # Process the file directly without saving to disk
#         result = await notification_service.upload_notifications_from_excel(
#             db, file_contents
#         )

#         return NotificationUploadSuccessResponse(
#             message="Notifications uploaded successfully",
#             detail="All notifications from the Excel file have been processed and created.",
#             result=result,
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Error uploading notifications: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Error uploading notifications: {str(e)}"
#         )
