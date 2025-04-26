import os

from app.configs.database import get_session
from app.services import script_service
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as HttpResponse

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
async def download_scripts(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_session)
):
    """
    Download all scripts as an Excel file.

    Returns:
        Excel file as a FileResponse
    """
    try:
        # Get the scripts data from the service
        file_path = await script_service.download_scripts_as_excel(db)
        if not file_path:
            raise HTTPException(status_code=404, detail="No scripts found")

        background_tasks.add_task(os.remove, file_path)
        return FileResponse(
            path=file_path,
            filename="Kịch bản.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        print(f"Error downloading scripts: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading scripts")


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
        await script_service.insert_scripts_from_excel(db, file_contents)

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
    script = await script_service.insert_script(db, body)
    return script


@router.put("/{script_id}")
async def update_script(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update an existing script in the database.
    """
    body = await request.json()
    script = await script_service.update_script(db, script_id, body)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.delete("/{script_id}")
async def delete_script(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a script from the database by its ID.
    """
    await script_service.delete_script(db, script_id)
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
    return HttpResponse(status_code=204)
