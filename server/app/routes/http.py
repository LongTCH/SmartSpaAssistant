import asyncio
import os

from app.configs import env_config
from app.configs.constants import SENTIMENTS
from app.configs.database import async_session, get_session
from app.services import (
    file_metadata_service,
    guest_service,
    messenger_service,
    script_service,
    sheet_service,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as HttpResponse

http_router = APIRouter()


@http_router.get("/")
def index():
    return {"message": "Facebook Messenger Webhook"}


@http_router.get("/webhooks/messenger")
async def get_webhook(request: Request):
    """
    Handle GET request for Facebook Messenger webhook verification.
    """

    # Parse the query params
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    # Checks if a token and mode is in the query string of the request
    if mode and token:
        # Checks the mode and token sent is correct
        if mode == "subscribe" and token == env_config.VERIFY_TOKEN:
            # Responds with the challenge token from the request
            print("WEBHOOK_VERIFIED")
            return HttpResponse(challenge)
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            raise HTTPException(status_code=403)

    # If mode or token is missing
    raise HTTPException(status_code=400)


@http_router.post("/webhooks/messenger")
async def post_webhook(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Handle POST request for Facebook Messenger webhook.
    """
    # Parse request body
    body = await request.json()
    # Checks this is an event from a page subscription
    if body.get("object") == "page":
        # Iterates over each entry - there may be multiple if batched
        for entry in body.get("entry", []):
            # Gets the body of the webhook event
            webhook_event = entry.get("messaging", [{}])[0]

            # Get the sender PSID
            sender_psid = webhook_event.get("sender", {}).get("id")
            receipient_psid = webhook_event.get("recipient", {}).get("id")
            timestamp = webhook_event.get("timestamp")

            # Chuyển xử lý message sang task riêng - create a copy of the db session
            session = async_session()
            task = asyncio.create_task(
                process_message_wrapper(
                    sender_psid, receipient_psid, timestamp, webhook_event, session
                )
            )
            # Add a done callback to ensure session is closed
            task.add_done_callback(
                lambda t: asyncio.create_task(close_session(session, t))
            )

        # Returns a '200 OK' response to all requests
        return HttpResponse()
    else:
        # Returns a '404 Not Found' if event is not from a page subscription
        raise HTTPException(status_code=404)


async def process_message_wrapper(
    sender_psid, receipient_psid, timestamp, webhook_event, db
):
    try:
        await messenger_service.process_message(
            sender_psid, receipient_psid, timestamp, webhook_event, db
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error in process_message_wrapper: {e}")


async def close_session(session, task):
    try:
        # Handle any exceptions from the task if needed
        if task.exception():
            print(f"Task raised an exception: {task.exception()}")
    finally:
        await session.close()


@http_router.post("/document_stores")
async def process_document_store(db: AsyncSession = Depends(get_session)):
    # Start the update process in a background task without waiting
    asyncio.create_task(file_metadata_service.update_knowledge(db))
    # await file_metadata_service.update_knowledge(db)
    return HttpResponse(status_code=200)


@http_router.get("/conversations")
async def get_conversations(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all conversations from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    assigned_to = request.query_params.get("assigned_to", "all")
    if assigned_to == "all":
        conversations = await guest_service.get_conversations(db, skip, limit)
        return conversations
    conversations = await guest_service.get_conversations_by_assignment(
        db, assigned_to, skip, limit
    )
    return conversations


@http_router.get("/conversations/sentiments")
async def get_conversations_by_sentiment(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Get conversations by sentiment from the database.
    """
    sentiment = request.query_params.get("sentiment", "neutral")
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))

    if sentiment not in [s.value for s in SENTIMENTS]:
        raise HTTPException(status_code=400, detail="Invalid sentiment value")

    conversations = await guest_service.get_paging_guests_by_sentiment(
        db, sentiment, skip, limit
    )
    return conversations


@http_router.patch("/conversations/{guest_id}/assignment")
async def update_assignment(
    guest_id: str, request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Update the assignment of a conversation.
    """
    body = await request.json()
    assigned_to = body.get("assigned_to")

    if not assigned_to:
        raise HTTPException(status_code=400, detail="assigned_to is required")

    guest = await guest_service.update_assignment(db, guest_id, assigned_to)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@http_router.get("/conversations/{guest_id}")
async def get_conversation_by_guest_id(
    request: Request, guest_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Get conversation by guest_id from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    conversations = await guest_service.get_chat_by_guest_id(db, guest_id, skip, limit)
    return conversations


@http_router.get("/scripts")
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


@http_router.get("/scripts/{script_id}")
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


@http_router.post("/scripts")
async def insert_script(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Insert a new script into the database.
    """
    body = await request.json()
    script = await script_service.insert_script(db, body)
    return script


@http_router.put("/scripts/{script_id}")
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


@http_router.delete("/scripts/{script_id}")
async def delete_script(
    request: Request, script_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a script from the database by its ID.
    """
    await script_service.delete_script(db, script_id)
    return HttpResponse(status_code=204)


@http_router.post("/scripts/delete-multiple")
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


@http_router.get("/sheets")
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


@http_router.get("/sheets/{sheet_id}")
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


@http_router.post("/sheets")
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
            "file": file_contents,
        }

        # Create new Sheet record using the service
        new_sheet = await sheet_service.insert_sheet(db, sheet_data)

        # Return the created sheet
        return new_sheet

    except Exception as e:
        print(f"Error creating sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing spreadsheet")


@http_router.put("/sheets/{sheet_id}")
async def update_sheet(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Update an existing sheet in the database.
    """
    body = await request.json()
    sheet = await sheet_service.update_sheet(db, sheet_id, body)
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")

    return sheet


@http_router.delete("/sheets/{sheet_id}")
async def delete_sheet(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    """
    Delete a sheet from the database by its ID.
    """
    await sheet_service.delete_sheet(db, sheet_id)
    return HttpResponse(status_code=204)


@http_router.post("/sheets/delete-multiple")
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
    return HttpResponse(status_code=204)


@http_router.get("/sheets/{sheet_id}/rows")
async def get_sheet_rows(
    request: Request, sheet_id: str, db: AsyncSession = Depends(get_session)
):
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    sheet_rows = await sheet_service.get_sheet_rows_by_sheet_id(
        db, sheet_id, skip, limit
    )
    return sheet_rows


@http_router.get("/sheets/{sheet_id}/download")
async def download_sheet(
    sheet_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    """
    Download a sheet as Excel file.

    Returns:
        Excel file as a FileResponse
    """
    try:
        # Get the sheet data from the service
        sheet = await sheet_service.get_sheet_by_id(db, sheet_id)
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")

        # Lưu và lấy đường dẫn file Excel
        file_path = await sheet_service.download_sheet_as_excel(db, sheet_id)
        background_tasks.add_task(os.remove, file_path)
        return FileResponse(
            path=file_path,
            filename=sheet["name"] + ".xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        print(f"Error downloading sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading sheet")
