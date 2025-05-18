import os

from app.configs.database import get_session
from app.services import notification_service
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.responses import Response as HttpResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all notifications from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    status = request.query_params.get("status", "all")
    if status == "all":
        notifications = await notification_service.get_notifications(db, page, limit)
        return notifications
    notifications = await notification_service.get_notifications_by_status(
        db, page, limit, status
    )
    return notifications


@router.get("/download-template")
async def get_notification_template(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_session)
):
    """
    Download an Excel template file for notifications.

    Returns:
        Excel template file as a FileResponse
    """
    try:
        # Get the template file path
        file_path = await notification_service.get_notification_template()

        # Schedule file cleanup after sending
        background_tasks.add_task(os.remove, file_path)

        return FileResponse(
            path=file_path,
            filename="notification_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        print(f"Error generating notification template: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating notification template"
        )


@router.get("/download")
async def download_notifications_as_excel(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    """
    Download all notifications as Excel file.

    Returns:
        Excel file as a FileResponse
    """
    try:
        # Get the file path from the service
        file_path = await notification_service.download_notifications_as_excel(db)

        # Schedule file cleanup after sending
        background_tasks.add_task(os.remove, file_path)

        return FileResponse(
            path=file_path,
            filename="Cài đặt thông báo.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        print(f"Error downloading notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading notifications")


@router.get("/{id}")
async def get_notification_by_id(id: str, db: AsyncSession = Depends(get_session)):
    """
    Get a notification by its ID from the database.
    """
    notification = await notification_service.get_notification_by_id(db, id)
    return notification


@router.post("")
async def insert_notification(
    notification: dict, db: AsyncSession = Depends(get_session)
):
    """
    Insert a new notification into the database.
    """
    await notification_service.insert_notification(db, notification)
    return HttpResponse(status_code=201)


@router.put("/{id}")
async def update_notification(
    id: str, notification: dict, db: AsyncSession = Depends(get_session)
):
    """
    Update a notification in the database.
    """
    await notification_service.update_notification(db, id, notification)
    return HttpResponse(status_code=204)


@router.delete("/{id}")
async def delete_notification(id: str, db: AsyncSession = Depends(get_session)):
    """
    Delete a notification from the database by its ID.
    """
    await notification_service.delete_notification(db, id)
    return HttpResponse(status_code=204)


@router.post("/delete-multiple")
async def delete_multiple_notifications(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple notifications from the database by their IDs.
    """
    body = await request.json()
    notification_ids = body.get("notification_ids", [])
    await notification_service.delete_multiple_notifications(db, notification_ids)
    return HttpResponse(status_code=204)


@router.post("/upload")
async def upload_notifications_excel(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Upload notifications from Excel file.
    The Excel file should have:
    1. 'data' sheet: Contains notifications with id, label, color, status, description, content
    2. 'n_{id}' sheets: One sheet per notification with its parameters

    Returns:
        Success message
    """
    try:
        # Parse the multipart form data
        form = await request.form()

        # Get the uploaded file
        file = form.get("file")

        if not file:
            raise HTTPException(status_code=400, detail="Missing required file")

        # Validate file is an Excel file
        content_type = file.content_type
        if content_type not in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only Excel files are supported.",
            )

        # Read file contents
        file_contents = await file.read()

        # Process the file directly without saving to disk
        result = await notification_service.upload_notifications_from_excel(
            db, file_contents
        )

        return {"message": "Notifications uploaded successfully", "result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error uploading notifications: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error uploading notifications: {str(e)}"
        )
