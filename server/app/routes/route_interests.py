from io import BytesIO
from typing import Optional
from urllib.parse import quote

from app.configs.database import get_session
from app.dtos import (
    ErrorDetail,
    InterestCreate,
    InterestCreateSuccessResponse,
    InterestDeleteMultipleRequest,
    InterestDeleteMultipleResponse,
    InterestUpdate,
    InterestUploadSuccessResponse,
    common_error_responses,
)
from app.services import interest_service
from app.validations.interest_validations import validate_interest_data
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response as HttpResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/interests", tags=["Interests"])


@router.get(
    "",
    summary="Get interests with pagination",
    description="Retrieves a paginated list of interests. Can be filtered by status.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved interests",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "limit": 10,
                        "total": 25,
                        "data": [
                            {
                                "id": "interest-123",
                                "name": "Công nghệ",
                                "description": "Sở thích về công nghệ và lập trình",
                                "status": "published",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T12:30:00Z",
                            }
                        ],
                        "has_next": True,
                        "has_prev": False,
                        "next_page": 2,
                        "prev_page": None,
                        "total_pages": 3,
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_interests(
    db: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status_filter: Optional[str] = Query(
        "all",
        alias="status",
        description="Filter interests by status ('published', 'draft', or 'all')",
    ),
):
    """
    Get interests from the database with pagination and status filtering.
    """
    if status_filter == "all":
        interests = await interest_service.get_interests(db, page, limit)
    else:
        interests = await interest_service.get_interests_by_status(
            db, page, limit, status_filter
        )
    return interests


@router.get(
    "/all-published",
    summary="Get all published interests",
    description="Retrieves a list of all interests that have the status 'published'.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved all published interests",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "interest-123",
                            "name": "Công nghệ",
                            "description": "Sở thích về công nghệ và lập trình",
                            "status": "published",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T12:30:00Z",
                        },
                        {
                            "id": "interest-124",
                            "name": "Du lịch",
                            "description": "Sở thích về du lịch và khám phá",
                            "status": "published",
                            "created_at": "2024-01-02T00:00:00Z",
                            "updated_at": "2024-01-02T12:30:00Z",
                        },
                    ]
                }
            },
        },
        **common_error_responses,
    },
)
async def get_all_published_interests(db: AsyncSession = Depends(get_session)):
    """
    Get all published interests from the database.
    """
    interests = await interest_service.get_all_interests_by_status(db, "published")
    return interests


@router.get(
    "/download",
    summary="Download all interests as Excel",
    description="Downloads all interests from the database as an Excel file.",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Excel file with interests.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorDetail,
            "description": "No interests found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error downloading interests",
        },
    },
)
async def download_interests(db: AsyncSession = Depends(get_session)):
    """
    Download all interests as an Excel file.
    """
    # Get the interests data from the service
    excel_buffer = await interest_service.download_interests_as_excel(db)
    if not excel_buffer:
        raise HTTPException(status_code=404, detail="No interests found")

    # StreamingResponse for better performance with large files
    response_buffer = BytesIO(excel_buffer.getvalue())

    # Encode the filename to handle non-ASCII characters
    filename = "Nhãn.xlsx"
    encoded_filename = quote(filename)

    # Return as streaming response with proper headers for Vietnamese filename
    return StreamingResponse(
        response_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
        },
    )


@router.get(
    "/download-template",
    summary="Download interest template",
    description="Downloads an Excel template file for interests.",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Excel template file for interests.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error generating interest template",
        },
    },
)
async def get_interest_template(db: AsyncSession = Depends(get_session)):
    """
    Download an Excel template file for interests.

    Returns:
        Excel template file as a StreamingResponse
    """
    # Get the template file path
    excel_buffer = await interest_service.get_interest_template()

    # StreamingResponse for better performance with large files
    response_buffer = BytesIO(excel_buffer.getvalue())

    # Encode the filename to handle non-ASCII characters
    filename = "Template Nhãn.xlsx"
    encoded_filename = quote(filename)

    # Return as streaming response with proper headers for Vietnamese filename
    return StreamingResponse(
        response_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
        },
    )


@router.get(
    "/{interest_id}",
    summary="Get interest by ID",
    description="Retrieves a specific interest by its ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved interest",
            "content": {
                "application/json": {
                    "example": {
                        "id": "interest-123",
                        "name": "Công nghệ",
                        "description": "Sở thích về công nghệ và lập trình",
                        "status": "published",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T12:30:00Z",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def get_interest_by_id(interest_id: str, db: AsyncSession = Depends(get_session)):
    """
    Get interest by interest_id from the database.
    """
    interest = await interest_service.get_interest_by_id(db, interest_id)
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    return interest


@router.post(
    "/upload",
    summary="Upload interests from Excel file",
    description="Uploads an Excel file containing interest data and creates new interests in the database.",
    responses={
        status.HTTP_200_OK: {
            "description": "Interests uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Interest data uploaded successfully",
                        "detail": "All interests from the Excel file have been processed and created.",
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorDetail,
            "description": "Invalid file type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid file type. Only Excel files are supported."
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def upload_interest(
    file: UploadFile = File(..., description="Excel file containing interest data"),
    db: AsyncSession = Depends(get_session),
):
    """
    Upload a interests sheet file and create new interests in the database.

    Expects multipart/form-data with:
    - file: Excel file
    """
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

    # Create new interests from Excel using the service
    await interest_service.insert_interests_from_excel(db, file_contents)

    # Return success response
    return InterestUploadSuccessResponse(
        message="Interest data uploaded successfully",
        detail="All interests from the Excel file have been processed and created.",
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new interest",
    description="Creates a new interest record in the database.",
)
async def insert_interest(
    interest_data: InterestCreate, db: AsyncSession = Depends(get_session)
):
    """
    Insert a new interest into the database.
    """
    # Validate interest data
    validation_errors = validate_interest_data(interest_data.model_dump())
    if validation_errors:
        raise HTTPException(status_code=400, detail={"errors": validation_errors})

    await interest_service.insert_interest(db, interest_data.model_dump())
    return InterestCreateSuccessResponse(
        message="Interest created successfully",
        detail="The new interest has been added to the database.",
    )


@router.put(
    "/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update an interest",
    description="Updates an existing interest by its ID.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Successfully updated interest"},
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorDetail,
            "description": "Interest not found",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorDetail,
            "description": "Invalid interest data",
        },
        **common_error_responses,
    },
)
async def update_interest(
    interest_id: str,
    interest_data: InterestUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    Update an existing interest in the database.
    """
    await interest_service.update_interest(
        db, interest_id, interest_data.model_dump(exclude_unset=True)
    )
    return HttpResponse(status_code=204)


@router.delete(
    "/{interest_id}",
    summary="Delete an interest",
    description="Deletes a specific interest by its ID.",
)
async def delete_interest(interest_id: str, db: AsyncSession = Depends(get_session)):
    """
    Delete a interest from the database by its ID.
    """
    await interest_service.delete_interest(db, interest_id)
    return HttpResponse(status_code=204)


@router.post(
    "/delete-multiple",
    summary="Delete multiple interests",
    description="Deletes multiple interests from the database by their IDs.",
    responses={
        status.HTTP_200_OK: {"description": "Successfully deleted interests"},
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorDetail,
            "description": "Invalid request data",
        },
        **common_error_responses,
    },
)
async def delete_multiple_interests(
    delete_request: InterestDeleteMultipleRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Delete multiple interests from the database by their IDs.
    """
    if not delete_request.interest_ids:
        raise HTTPException(status_code=400, detail="interest_ids is required")

    await interest_service.delete_multiple_interests(db, delete_request.interest_ids)
    return InterestDeleteMultipleResponse(
        message="Interests deleted successfully",
        detail=f"Successfully deleted {len(delete_request.interest_ids)} interests from the database.",
        deleted_count=len(delete_request.interest_ids),
    )
