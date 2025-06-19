from app.configs.database import get_session
from app.dtos import ErrorDetail
from app.services import sheet_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v2/sheets", tags=["Sheets"])


@router.get(
    "",
    summary="Get sheets with pagination",
    description="Retrieves a paginated list of sheets. Can be filtered by status.",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved sheets",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "limit": 10,
                        "total": 20,
                        "data": [
                            {
                                "id": "sheet-123",
                                "name": "Bảng dữ liệu khách hàng",
                                "description": "Bảng chứa thông tin khách hàng",
                                "status": "published",
                                "column_config": [
                                    {
                                        "name": "name",
                                        "display_name": "Tên",
                                        "data_type": "String",
                                        "is_required": True,
                                        "is_index": False,
                                    }
                                ],
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Error fetching sheets",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error fetching sheets: Database connection failed"
                    }
                }
            },
        },
    },
)
async def get_sheets(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status: str = Query(
        "all", description="Filter by status: 'all', 'published', 'draft', 'archived'"
    ),
    db: AsyncSession = Depends(get_session),
):
    """
    Get paginated list of sheets from the database.
    """
    try:
        if status == "all":
            sheets_page = await sheet_service.get_sheets(db, page, limit)
        else:
            sheets_page = await sheet_service.get_sheets_by_status(
                db, page, limit, status
            )

        # Return the original format - sheets_page is a PaginationDto that contains the data
        return sheets_page

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sheets: {str(e)}")


@router.get("/{sheet_id}")
async def get_sheet_by_id(sheet_id: str, db: AsyncSession = Depends(get_session)):
    """
    Get sheet by sheet_id from the database.
    """
    sheet = await sheet_service.get_sheet_by_id(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")
    return sheet


# @router.post("", status_code=201)
# async def create_sheet(
#     name: str = Form(..., description="Name of the sheet"),
#     description: str = Form(..., description="Description of the sheet"),
#     status: str = Form(
#         "published", description="Status of the sheet (published or draft)"
#     ),
#     column_config: str = Form(None, description="JSON string of column configuration"),
#     file: UploadFile = File(..., description="Excel file to upload"),
#     db: AsyncSession = Depends(get_session),
# ):
#     """
#     Upload a spreadsheet file and create a new sheet in the database.

#     Expects multipart/form-data with:
#     - **name**: Name of the sheet
#     - **description**: Description of the sheet
#     - **status**: Status of the sheet (published or draft)
#     - **column_config**: Optional JSON string of column configuration
#     - **file**: Excel file (.xlsx or .xls)

#     Returns the ID of the created sheet.
#     """
#     try:
#         # Validate required fields
#         if not name or not description or not file:
#             raise HTTPException(status_code=400, detail="Missing required fields")

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

#         # Validate sheet data using Pydantic
#         try:
#             validated_sheet_data = validate_sheet_creation_data(
#                 name, description, column_config, status
#             )
#         except ValueError as e:
#             raise HTTPException(status_code=400, detail=str(e))
#         except ValidationError as e:
#             raise HTTPException(
#                 status_code=400, detail=f"Validation error: {str(e)}"
#             )  # Prepare sheet data
#         sheet_data = {
#             "name": validated_sheet_data.name,
#             "description": validated_sheet_data.description,
#             "status": validated_sheet_data.status,
#             "column_config": json.dumps(
#                 [col.model_dump() for col in validated_sheet_data.column_config]
#             ),
#             "file": file_contents,
#         }  # Create new Sheet record using the service
#         new_sheet_id = await sheet_service.insert_sheet(db, sheet_data)

#         # Index the sheet for search (background task)
#         asyncio_utils.run_background(sheet_rag_service.insert_sheet, new_sheet_id)

#         return new_sheet_id

#     except HTTPException:
#         # Re-raise HTTPExceptions (like validation errors) without modification
#         raise
#     except Exception as e:
#         print(f"Error creating sheet: {e}")
#         raise HTTPException(status_code=500, detail=f"Error processing spreadsheet")


# @router.put("/{sheet_id}")
# async def update_sheet(
#     sheet_id: str, sheet_data: SheetUpdate, db: AsyncSession = Depends(get_session)
# ):
#     """
#     Update an existing sheet in the database.
#     """
#     # Convert Pydantic model to dict, excluding None values
#     update_data = sheet_data.model_dump(exclude_unset=True)

#     # Convert column_config if present
#     if "column_config" in update_data and update_data["column_config"]:
#         update_data["column_config"] = [
#             col.dict() if hasattr(col, "dict") else col
#             for col in update_data["column_config"]
#         ]

#     await sheet_service.update_sheet(db, sheet_id, update_data)
#     return HttpResponse(status_code=204)


# @router.delete("/{sheet_id}")
# async def delete_sheet(sheet_id: str, db: AsyncSession = Depends(get_session)):
#     """
#     Delete a sheet from the database by its ID.
#     """
#     try:
#         await sheet_service.delete_sheet(db, sheet_id)
#         asyncio_utils.run_background(sheet_rag_service.delete_sheet, sheet_id)
#         return HttpResponse(status_code=204)
#     except Exception as e:
#         print(f"Error deleting sheet: {e}")
#         # Vẫn trả về 204 vì việc xóa không tìm thấy sheet cũng được coi là thành công
#         # Điều này phù hợp với nguyên tắc thiết kế API idempotent
#         return HttpResponse(status_code=204)


# @router.post("/delete-multiple")
# async def delete_multiple_sheets(
#     request_data: SheetDeleteMultipleRequest, db: AsyncSession = Depends(get_session)
# ):
#     """
#     Delete multiple sheets from the database by their IDs.
#     """
#     sheet_ids = request_data.sheet_ids
#     await sheet_service.delete_multiple_sheets(db, sheet_ids)
#     asyncio_utils.run_background(sheet_rag_service.delete_sheets, sheet_ids)
#     return HttpResponse(status_code=204)


@router.get("/{sheet_id}/rows")
async def get_sheet_rows(
    sheet_id: str,
    skip: int = Query(0, ge=0, description="Number of rows to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of rows to return"),
    db: AsyncSession = Depends(get_session),
):
    """
    Get paginated rows from a specific sheet.
    """
    sheet_rows = await sheet_service.get_sheet_rows_by_sheet_id(
        db, sheet_id, skip, limit
    )
    return sheet_rows


# @router.get("/{sheet_id}/download")
# async def download_sheet(sheet_id: str, db: AsyncSession = Depends(get_session)):
#     """
#     Download a sheet as an Excel file.

#     Returns:
#         Excel file as a StreamingResponse
#     """
#     try:
#         # Get the sheet data from the service
#         sheet = await sheet_service.get_sheet_by_id(db, sheet_id)
#         if not sheet:
#             raise HTTPException(status_code=404, detail="Sheet not found")

#         # Get the Excel file buffer from the service
#         excel_buffer = await sheet_service.download_sheet_as_excel_stream(db, sheet_id)

#         # Create a new BytesIO to avoid any potential issues with the original buffer
#         response_buffer = BytesIO(excel_buffer.getvalue())

#         # Encode the filename to handle non-ASCII characters
#         filename = f"{sheet['name']}.xlsx"
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
#         print(f"Error downloading sheets: {e}")  # Updated error message
#         import traceback

#         traceback.print_exc()
#         raise HTTPException(
#             status_code=500, detail=f"Error downloading sheets: {str(e)}"
#         )  # Updated error message
