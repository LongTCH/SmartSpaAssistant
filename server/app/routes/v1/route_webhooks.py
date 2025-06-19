from typing import Optional

from app.configs import env_config
from app.dtos import common_error_responses
from app.services.integrations import messenger_service
from app.utils import asyncio_utils
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from fastapi.responses import Response as HttpResponse

router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])


@router.get(
    "/messenger",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Facebook Messenger webhook",
    description="""
    Handle GET request for Facebook Messenger webhook verification.
    
    This endpoint is called by Facebook to verify the webhook URL during setup.
    It validates the verification token and responds with the challenge parameter
    if the token matches.
    
    **Facebook Webhook Verification Process:**
    1. Facebook sends a GET request with verification parameters
    2. Server validates the `hub.verify_token` against configured token
    3. If valid, server responds with the `hub.challenge` value
    4. Facebook completes webhook registration
    """,
    responses={
        200: {
            "description": "Webhook verified successfully - returns challenge string",
            "content": {"text/plain": {"example": "1234567890"}},
        },
        400: {
            "description": "Missing required verification parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Missing hub.mode or hub.verify_token parameters"
                    }
                }
            },
        },
        403: {
            "description": "Invalid verification token",
            "content": {"application/json": {"example": {"detail": "Forbidden"}}},
        },
        **common_error_responses,
    },
)
async def get_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(
        None, alias="hub.mode", description="Webhook subscription mode"
    ),
    hub_verify_token: Optional[str] = Query(
        None, alias="hub.verify_token", description="Verification token"
    ),
    hub_challenge: Optional[str] = Query(
        None, alias="hub.challenge", description="Challenge string to echo back"
    ),
):
    """
    Handle GET request for Facebook Messenger webhook verification.
    """

    # Parse the query params (fallback if Query params don't work with aliases)
    if not hub_mode or not hub_verify_token or not hub_challenge:
        query_params = request.query_params
        hub_mode = query_params.get("hub.mode")
        hub_verify_token = query_params.get("hub.verify_token")
        hub_challenge = query_params.get("hub.challenge")

    # Checks if a token and mode is in the query string of the request
    if hub_mode and hub_verify_token:
        # Checks the mode and token sent is correct
        if hub_mode == "subscribe" and hub_verify_token == env_config.VERIFY_TOKEN:
            # Responds with the challenge token from the request
            print("WEBHOOK_VERIFIED")
            return PlainTextResponse(hub_challenge)
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification token or mode",
            )

    # If mode or token is missing
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing required parameters: hub.mode, hub.verify_token, or hub.challenge",
    )


@router.post(
    "/messenger",
    status_code=status.HTTP_200_OK,
    summary="Handle Facebook Messenger webhook events",
    description="""
    Handle POST request for Facebook Messenger webhook events.
    
    This endpoint receives webhook events from Facebook Messenger when users
    interact with the connected page. It processes various event types including
    messages, postbacks, and other interactions.
    
    **Event Processing:**
    1. Validates the webhook payload structure
    2. Extracts sender, recipient, and event data
    3. Processes events asynchronously in background tasks
    4. Returns immediate acknowledgment to Facebook
    
    **Supported Event Types:**
    - Text messages from users
    - Postback events from interactive elements
    - Quick reply responses
    - Delivery confirmations
    
    **Background Processing:**
    Events are processed asynchronously to ensure fast response times
    and prevent Facebook webhook timeouts.
    """,
    responses={
        200: {
            "description": "Webhook event received and queued for processing",
            "content": {"application/json": {"example": {"status": "success"}}},
        },
        400: {
            "description": "Invalid webhook payload structure",
            "content": {
                "application/json": {"example": {"detail": "Invalid JSON payload"}}
            },
        },
        404: {
            "description": "Webhook event is not from a page subscription",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not Found - Event not from page subscription"
                    }
                }
            },
        },
        **common_error_responses,
    },
)
async def post_webhook(request: Request):
    """
    Handle POST request for Facebook Messenger webhook events.
    """
    try:
        # Parse request body
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}",
        )

    # Checks this is an event from a page subscription
    if body.get("object") == "page":
        # Iterates over each entry - there may be multiple if batched
        for entry in body.get("entry", []):
            # Gets the body of the webhook event
            messaging_events = entry.get("messaging", [])

            for webhook_event in messaging_events:
                # Get the sender PSID
                sender_psid = webhook_event.get("sender", {}).get("id")
                recipient_psid = webhook_event.get("recipient", {}).get("id")
                timestamp = webhook_event.get("timestamp")

                if sender_psid and recipient_psid and timestamp:
                    # Process message in background task - create a copy of the db session
                    asyncio_utils.run_background(
                        messenger_service.process_message,
                        sender_psid,
                        recipient_psid,
                        timestamp,
                        webhook_event,
                    )
                else:
                    print(f"Warning: Incomplete webhook event data: {webhook_event}")

        # Returns a '200 OK' response to all requests
        return HttpResponse()
    else:
        # Returns a '404 Not Found' if event is not from a page subscription
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event is not from a page subscription",
        )
