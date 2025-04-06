from fastapi import APIRouter, Request, HTTPException, Depends, Form
from typing import Annotated
from starlette.responses import Response as HttpResponse
from app.configs import env_config
from app.configs.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import chat_service, file_metadata_service
import asyncio

router = APIRouter()


@router.get("/")
def index():
    return {"message": "Facebook Messenger Webhook"}


@router.get("/webhooks/messenger")
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


@router.post("/webhooks/messenger")
async def post_webhook(request: Request):
    """
    Handle POST request for Facebook Messenger webhook.
    """
    # Parse request body
    body = await request.json()
    print(body)
    # Checks this is an event from a page subscription
    if body.get("object") == "page":
        # Iterates over each entry - there may be multiple if batched
        for entry in body.get("entry", []):
            # Gets the body of the webhook event
            webhook_event = entry.get("messaging", [{}])[0]

            # Get the sender PSID
            sender_psid = webhook_event.get("sender", {}).get("id")

            # Chuyển xử lý message sang task riêng
            asyncio.create_task(chat_service.process_message(
                sender_psid, webhook_event))

        # Returns a '200 OK' response to all requests
        return HttpResponse()
    else:
        # Returns a '404 Not Found' if event is not from a page subscription
        raise HTTPException(status_code=404)


@router.post("/document_stores")
async def process_document_store(db: AsyncSession = Depends(get_db)):
    # Start the update process in a background task without waiting
    asyncio.create_task(file_metadata_service.update_knowledge(db))
    # await file_metadata_service.update_knowledge(db)
    return HttpResponse(status_code=200)
