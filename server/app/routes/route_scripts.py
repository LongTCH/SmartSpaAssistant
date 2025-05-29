from io import BytesIO
from urllib.parse import quote

from app.configs.database import get_session
from app.services import script_service
from app.services.integrations import script_rag_service
from app.utils import asyncio_utils
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response as HttpResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scripts", tags=["Scripts"])


@router.get("")
async def get_scripts(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all scripts from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    status = request.query_params.get("status", "all")
    if status == "all":
        scripts = await script_service.get_scripts(db, page, limit)
        return scripts
    scripts = await script_service.get_scripts_by_status(db, page, limit, status)
    return scripts


@router.get("/all-published")
async def get_all_published_scripts(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Get all published scripts from the database.
    """

    scripts = await script_service.get_all_published_scripts(db)
    return scripts


@router.get("/download")
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


@router.get("/download-template")
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


@router.get("/{script_id}")
async def get_script_by_id(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get script by script_id from the database.
    """
    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post("/upload")
async def upload_script(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Upload a scripts sheet file and create new scripts in the database.

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
        script_ids = await script_service.insert_scripts_from_excel(db, file_contents)
        asyncio_utils.run_background(script_rag_service.insert_scripts, script_ids)
        # Return the created sheet
        return HttpResponse(status_code=201)

    except Exception as e:
        print(f"Error creating script: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing spreadsheet")


@router.post("")
async def insert_script(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Insert a new script into the database.
    """
    body = await request.json()
    new_script_id = await script_service.insert_script(db, body)
    asyncio_utils.run_background(script_rag_service.insert_script, new_script_id)
    return HttpResponse(status_code=201)


@router.put("/{script_id}")
async def update_script(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update an existing script in the database.
    """
    body = await request.json()
    await script_service.update_script(db, script_id, body)
    asyncio_utils.run_background(script_rag_service.update_script, script_id)
    return HttpResponse(status_code=204)


@router.delete("/{script_id}")
async def delete_script(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a script from the database by its ID.
    """
    await script_service.delete_script(db, script_id)
    asyncio_utils.run_background(script_rag_service.delete_script, script_id)
    return HttpResponse(status_code=204)


@router.post("/delete-multiple")
async def delete_multiple_scripts(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple scripts from the database by their IDs.
    """
    body = await request.json()
    script_ids = body.get("script_ids", [])
    if not script_ids:
        raise HTTPException(status_code=400, detail="script_ids is required")
    await script_service.delete_multiple_scripts(db, script_ids)
    asyncio_utils.run_background(script_rag_service.delete_scripts, script_ids)
    return HttpResponse(status_code=204)
