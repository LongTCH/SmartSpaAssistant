from io import BytesIO
from typing import Optional
from urllib.parse import quote

from app.configs.database import get_session
from app.dtos import (
    ErrorDetail,
    ScriptCreate,
    ScriptDeleteMultipleRequest,
    ScriptUpdate,
    UploadSuccessResponse,
    common_error_responses,
)
from app.services import script_service
from app.services.integrations import script_rag_service
from app.utils import asyncio_utils
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response as HttpResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scripts", tags=["Scripts"])


@router.get(
    "",
    summary="Get scripts with pagination",
    description="Retrieves a paginated list of scripts. Can be filtered by status.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved scripts",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "limit": 10,
                        "total": 30,
                        "data": [
                            {
                                "id": "script-123",
                                "title": "Kịch bản chăm sóc khách hàng",
                                "content": "Xin chào, tôi có thể giúp gì cho bạn hôm nay?",
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
async def get_scripts(
    db: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status_filter: Optional[str] = Query(
        "all",
        alias="status",
        description="Filter scripts by status ('published', 'draft', or 'all')",
    ),
):
    """
    Get scripts from the database with pagination and status filtering.
    """
    if status_filter == "all":
        scripts_page = await script_service.get_scripts(db, page, limit)
    else:
        scripts_page = await script_service.get_scripts_by_status(
            db, page, limit, status_filter
        )
    return scripts_page


@router.get(
    "/all-published",
    summary="Get all published scripts",
    description="Retrieves a list of all scripts that have the status 'published'.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved all published scripts",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "script-123",
                            "title": "Kịch bản chăm sóc khách hàng",
                            "content": "Xin chào, tôi có thể giúp gì cho bạn hôm nay?",
                            "status": "published",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T12:30:00Z",
                        },
                        {
                            "id": "script-124",
                            "title": "Kịch bản giải quyết khiếu nại",
                            "content": "Tôi hiểu sự bức xúc của bạn. Hãy để tôi giúp bạn giải quyết vấn đề này.",
                            "status": "published",
                            "created_at": "2024-01-02T00:00:00Z",
                            "updated_at": "2024-01-02T12:30:00Z",
                        },
                    ]
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: common_error_responses[
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ],
    },
)
async def get_all_published_scripts(db: AsyncSession = Depends(get_session)):
    """
    Get all published scripts from the database.
    """
    scripts = await script_service.get_all_published_scripts(db)
    return scripts


@router.get(
    "/download",
    summary="Download all scripts as Excel",
    description="Downloads all scripts from the database as an Excel file.",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Excel file with scripts.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorDetail,
            "description": "No scripts found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error downloading scripts",
        },
    },
)
async def download_scripts(db: AsyncSession = Depends(get_session)):
    """
    Download all scripts as an Excel file.

    Returns:
        Excel file as a StreamingResponse
    """
    try:
        # Get the scripts data from the service as BytesIO
        excel_buffer = await script_service.download_scripts_as_excel_stream(db)
        if not excel_buffer:
            raise HTTPException(status_code=404, detail="No scripts found")

        # Create a new BytesIO to avoid any potential issues with the original buffer
        response_buffer = BytesIO(excel_buffer.getvalue())

        # Encode the filename to handle non-ASCII characters
        filename = "Kịch bản.xlsx"
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
    except Exception as e:
        print(f"Error downloading scripts: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error downloading scripts: {str(e)}"
        )


@router.get(
    "/download-template",
    summary="Download script template",
    description="Downloads an Excel template file for scripts.",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Excel template file for scripts.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error generating script template",
        },
    },
)
# db might not be needed if template is static
async def get_script_template(db: AsyncSession = Depends(get_session)):
    """
    Download an Excel template file for scripts.

    Returns:
        Excel template file as a StreamingResponse
    """
    try:
        # Get the template file as BytesIO
        excel_buffer = await script_service.get_script_template()

        # Encode the filename to handle non-ASCII characters
        filename = "Template Kịch bản.xlsx"
        encoded_filename = quote(filename)

        # Return as streaming response with proper headers for Vietnamese filename
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
            },
        )
    except Exception as e:
        print(f"Error generating script template: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating script template: {str(e)}"
        )


@router.get(
    "/{script_id}",
    summary="Get script by ID",
    description="Retrieves a specific script by its ID.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved script",
            "content": {
                "application/json": {
                    "example": {
                        "id": "script-123",
                        "title": "Kịch bản chăm sóc khách hàng",
                        "content": "Xin chào, tôi có thể giúp gì cho bạn hôm nay?",
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
async def get_script_by_id(script_id: str, db: AsyncSession = Depends(get_session)):
    """
    Get script by script_id from the database.
    """
    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload scripts from Excel",
    description="Uploads an Excel file, processes it, and creates new scripts. Returns IDs of created scripts.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Scripts uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Scripts uploaded successfully.",
                        "script_ids": ["script-123", "script-124", "script-125"],
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorDetail,
            "description": "Missing file or invalid file type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid file type. Only Excel files are supported."
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error processing spreadsheet",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing Excel file"}
                }
            },
        },
    },
)
async def upload_script(
    db: AsyncSession = Depends(get_session),
    file: UploadFile = File(
        ..., description="Excel file containing scripts to upload."
    ),
):
    """
    Upload a scripts sheet file and create new scripts in the database.

    Expects multipart/form-data with:
    - file: Excel file
    """
    try:
        if not file:  # Should be caught by FastAPI if File(...) is used
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided."
            )

        content_type = file.content_type
        if content_type not in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only Excel files (.xls, .xlsx) are supported.",
            )

        file_contents = await file.read()
        script_ids = await script_service.insert_scripts_from_excel(db, file_contents)
        asyncio_utils.run_background(script_rag_service.insert_scripts, script_ids)
        return UploadSuccessResponse(
            message="Scripts uploaded successfully.", script_ids=script_ids
        )

    except (
        HTTPException
    ):  # Re-raise HTTPException to be handled by FastAPI and middleware
        raise
    except Exception as e:
        print(f"Error creating script from upload: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing spreadsheet",
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Insert a new script",
    description="Inserts a new script into the database. Script data is validated by the ScriptCreate schema.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Script created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "script-123",
                        "title": "Kịch bản mới",
                        "content": "Nội dung kịch bản mới được tạo",
                        "status": "draft",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def insert_script(
    script_data: ScriptCreate, db: AsyncSession = Depends(get_session)
):
    """
    Insert a new script into the database.
    """
    try:
        new_script_id = await script_service.insert_script(db, script_data.model_dump())
        asyncio_utils.run_background(script_rag_service.insert_script, new_script_id)

        created_script = await script_service.get_script_by_id(db, new_script_id)
        if not created_script:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created script.",
            )
        return created_script
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inserting script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting script: {str(e)}",
        )


@router.put(
    "/{script_id}",
    summary="Update an existing script",
    description="Updates an existing script by its ID. Only provided fields will be updated.",
    responses={
        status.HTTP_200_OK: {
            "description": "Script updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "script-123",
                        "title": "Kịch bản đã cập nhật",
                        "content": "Nội dung kịch bản đã được cập nhật",
                        "status": "published",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T15:30:00Z",
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def update_script(
    script_id: str,
    script_data: ScriptUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    Update an existing script in the database.
    """
    try:
        await script_service.update_script(
            db, script_id, script_data.model_dump(exclude_unset=True)
        )
        asyncio_utils.run_background(script_rag_service.update_script, script_id)

        updated_script = await script_service.get_script_by_id(db, script_id)
        if not updated_script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found after update attempt.",
            )
        return updated_script
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating script {script_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating script: {str(e)}",
        )


@router.delete(
    "/{script_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a script by ID",
    description="Deletes a specific script from the database by its ID.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Script deleted successfully"},
        status.HTTP_404_NOT_FOUND: common_error_responses[status.HTTP_404_NOT_FOUND],
        status.HTTP_500_INTERNAL_SERVER_ERROR: common_error_responses[
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ],
    },
)
async def delete_script(script_id: str, db: AsyncSession = Depends(get_session)):
    """
    Delete a script from the database by its ID.
    """
    try:
        await script_service.delete_script(db, script_id)
        asyncio_utils.run_background(script_rag_service.delete_script, script_id)
        return HttpResponse(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:  # If service raises HTTPException (e.g. 404)
        raise
    except Exception as e:  # Catch other potential errors
        print(f"Error deleting script {script_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting script: {str(e)}",
        )


@router.post(
    "/delete-multiple",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete multiple scripts",
    description="Deletes multiple scripts from the database based on a list of IDs.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Scripts deleted successfully"},
        # Corrected to use the model from common_error_responses
        status.HTTP_400_BAD_REQUEST: common_error_responses[
            status.HTTP_400_BAD_REQUEST
        ],
        status.HTTP_500_INTERNAL_SERVER_ERROR: common_error_responses[
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ],
    },
)
async def delete_multiple_scripts(
    payload: ScriptDeleteMultipleRequest, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple scripts from the database by their IDs.
    """
    try:
        script_ids = payload.script_ids
        # Pydantic model should ensure script_ids is present, but could be empty list.
        if not script_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="script_ids list cannot be empty.",
            )

        await script_service.delete_multiple_scripts(db, script_ids)
        asyncio_utils.run_background(script_rag_service.delete_scripts, script_ids)
        return HttpResponse(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting multiple scripts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting multiple scripts: {str(e)}",
        )
