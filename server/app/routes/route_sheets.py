from io import BytesIO
from urllib.parse import quote

from app.configs.database import get_session
from app.services import sheet_service
from app.services.integrations import sheet_rag_service
from app.utils import asyncio_utils
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response as HttpResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/sheets", tags=["Sheets"])


@router.get("")
async def get_sheets(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all sheets from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    status = request.query_params.get("status", "all")
    if status == "all":
        sheets = await sheet_service.get_sheets(db, page, limit)
        return sheets
    sheets = await sheet_service.get_sheets_by_status(db, page, limit, status)
    return sheets


@router.get("/{sheet_id}")
async def get_sheet_by_id(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get sheet by sheet_id from the database.
    """
    sheet = await sheet_service.get_sheet_by_id(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")
    return sheet


@router.post("")
async def create_sheet(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Upload a spreadsheet file and create a new sheet in the database.

    Expects multipart/form-data with:
    - name: Name of the sheet
    - description: Description of the sheet
    - status: Status of the sheet (published or draft)
    - file: Excel file
    """
    try:
        # Parse the multipart form data
        form = await request.form()

        # Get form fields
        name = form.get("name")
        description = form.get("description")
        status = form.get("status", "published")
        column_config = form.get("column_config")

        # Get the uploaded file
        file = form.get("file")

        if not name or not description or not file:
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

        # Process the sheet data in the service layer
        sheet_data = {
            "name": name,
            "description": description,
            "status": status,
            "column_config": column_config,
            "file": file_contents,
        }

        # Create new Sheet record using the service
        new_sheet_id = await sheet_service.insert_sheet(db, sheet_data)

        asyncio_utils.run_background(sheet_rag_service.insert_sheet, new_sheet_id)
        return new_sheet_id

    except Exception as e:
        print(f"Error creating sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing spreadsheet")


@router.put("/{sheet_id}")
async def update_sheet(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update an existing sheet in the database.
    """
    body = await request.json()
    await sheet_service.update_sheet(db, sheet_id, body)
    return HttpResponse(status_code=204)


@router.delete("/{sheet_id}")
async def delete_sheet(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a sheet from the database by its ID.
    """
    try:
        await sheet_service.delete_sheet(db, sheet_id)
        asyncio_utils.run_background(sheet_rag_service.delete_sheet, sheet_id)
        return HttpResponse(status_code=204)
    except Exception as e:
        print(f"Error deleting sheet: {e}")
        # Vẫn trả về 204 vì việc xóa không tìm thấy sheet cũng được coi là thành công
        # Điều này phù hợp với nguyên tắc thiết kế API idempotent
        return HttpResponse(status_code=204)


@router.post("/delete-multiple")
async def delete_multiple_sheets(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple sheets from the database by their IDs.
    """
    body = await request.json()
    sheet_ids = body.get("sheet_ids", [])
    if not sheet_ids:
        raise HTTPException(status_code=400, detail="sheet_ids is required")
    await sheet_service.delete_multiple_sheets(db, sheet_ids)
    asyncio_utils.run_background(sheet_rag_service.delete_sheets, sheet_ids)
    return HttpResponse(status_code=204)


@router.get("/{sheet_id}/rows")
async def get_sheet_rows(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    sheet_rows = await sheet_service.get_sheet_rows_by_sheet_id(
        db, sheet_id, skip, limit
    )
    return sheet_rows


@router.get("/{sheet_id}/download")
async def download_sheet(
    sheet_id: str, request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Download multiple sheets as a single Excel file.

    Returns:
        Excel file as a StreamingResponse
    """
    try:
        # Get query parameters
        # Get the sheet data from the service
        sheet = await sheet_service.get_sheet_by_id(db, sheet_id)
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")

        # Get the Excel file buffer from the service
        excel_buffer = await sheet_service.download_sheet_as_excel_stream(db, sheet_id)

        # Create a new BytesIO to avoid any potential issues with the original buffer
        response_buffer = BytesIO(excel_buffer.getvalue())

        # Encode the filename to handle non-ASCII characters
        filename = f"{sheet['name']}.xlsx"
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
        print(f"Error downloading sheets: {e}")  # Updated error message
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error downloading sheets: {str(e)}"
        )  # Updated error message
