from fastapi import APIRouter, Request, HTTPException, Depends, Form
from typing import Annotated
from starlette.responses import Response as HttpResponse
from app.configs import env_config
from app.configs.database import get_session, async_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import conversation_service, file_metadata_service, messenger_service
import asyncio

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
                process_message_wrapper(sender_psid, receipient_psid, timestamp, webhook_event, session)
            )
            # Add a done callback to ensure session is closed
            task.add_done_callback(lambda t: asyncio.create_task(close_session(session, t)))

        # Returns a '200 OK' response to all requests
        return HttpResponse()
    else:
        # Returns a '404 Not Found' if event is not from a page subscription
        raise HTTPException(status_code=404)

async def process_message_wrapper(sender_psid, receipient_psid, timestamp, webhook_event, db):
    try:
        await messenger_service.process_message(sender_psid, receipient_psid, timestamp, webhook_event, db)
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
    conversations = await conversation_service.get_conversations(db, skip, limit)
    return conversations


@http_router.get("/conversations/{guest_id}")
async def get_conversation_by_guest_id(request: Request, guest_id: str, db: AsyncSession = Depends(get_session)):
    """
    Get conversation by guest_id from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    conversations = await conversation_service.get_chat_by_guest_id(db, guest_id, skip, limit)
    return conversations
