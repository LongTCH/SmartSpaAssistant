import os

from app.configs.database import get_session
from app.services import interest_service
from app.utils import asyncio_utils
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as HttpResponse

router = APIRouter(prefix="/interests", tags=["Interests"])


@router.get("")
async def get_interests(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all interests from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    status = request.query_params.get("status", "all")
    if status == "all":
        interests = await interest_service.get_interests(db, page, limit)
        return interests
    interests = await interest_service.get_interests_by_status(db, page, limit, status)
    return interests


@router.get("/all-published")
async def get_all_published_interests(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Get all published interests from the database.
    """
    interests = await interest_service.get_all_interests_by_status(db, "published")
    return interests


@router.get("/download")
async def download_interests(db: AsyncSession = Depends(get_session)):
    """
    Download all interests as an Excel file.

    Returns:
        Excel file as a FileResponse
    """
    try:
        # Get the interests data from the service
        file_path = await interest_service.download_interests_as_excel(db)
        if not file_path:
            raise HTTPException(status_code=404, detail="No interests found")

        asyncio_utils.run_background(os.remove, file_path)
        return FileResponse(
            path=file_path,
            filename="Xu hướng Khách hàng.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        print(f"Error downloading interests: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading interests")


@router.get("/{interest_id}")
async def get_interest_by_id(
    request: Request, interest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get interest by interest_id from the database.
    """
    interest = await interest_service.get_interest_by_id(db, interest_id)
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    return interest


@router.post("/upload")
async def upload_interest(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Upload a interests sheet file and create new interests in the database.

    Expects multipart/form-data with:
    - file: Excel file
    """
    try:
        # Parse the multipart form data
        form = await request.form()

        # Get the uploaded file
        file = form.get("file")

        if not file:
            raise HTTPException(status_code=400, detail="Missing required fields")

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

        # Create new Sheet record using the service
        await interest_service.insert_interests_from_excel(db, file_contents)

        # Return the created sheet
        return HttpResponse(status_code=201)

    except Exception as e:
        print(f"Error creating interest: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing spreadsheet")


@router.post("")
async def insert_interest(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Insert a new interest into the database.
    """
    body = await request.json()
    await interest_service.insert_interest(db, body)
    return HttpResponse(status_code=201)


@router.put("/{interest_id}")
async def update_interest(
    request: Request, interest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update an existing interest in the database.
    """
    body = await request.json()
    await interest_service.update_interest(db, interest_id, body)
    return HttpResponse(status_code=204)


@router.delete("/{interest_id}")
async def delete_interest(
    request: Request, interest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a interest from the database by its ID.
    """
    await interest_service.delete_interest(db, interest_id)
    return HttpResponse(status_code=204)


@router.post("/delete-multiple")
async def delete_multiple_interests(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple interests from the database by their IDs.
    """
    body = await request.json()
    interest_ids = body.get("interest_ids", [])
    if not interest_ids:
        raise HTTPException(status_code=400, detail="interest_ids is required")
    await interest_service.delete_multiple_interests(db, interest_ids)
    return HttpResponse(status_code=204)
