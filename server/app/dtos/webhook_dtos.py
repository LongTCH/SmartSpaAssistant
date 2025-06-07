from typing import List, Optional

from pydantic import BaseModel, Field


class MessengerSenderDto(BaseModel):
    """Messenger sender information."""

    id: str = Field(
        description="Sender PSID (Page-Scoped ID)", example="1234567890123456"
    )


class MessengerRecipientDto(BaseModel):
    """Messenger recipient information."""

    id: str = Field(
        description="Recipient PSID (Page-Scoped ID)", example="9876543210987654"
    )


class MessengerMessageDto(BaseModel):
    """Messenger message content."""

    mid: Optional[str] = Field(
        None, description="Message ID", example="m_1234567890123456"
    )
    text: Optional[str] = Field(
        None, description="Message text content", example="Hello, how can I help you?"
    )


class MessengerWebhookEventDto(BaseModel):
    """Single messenger webhook event."""

    sender: MessengerSenderDto = Field(description="Sender information")
    recipient: MessengerRecipientDto = Field(description="Recipient information")
    timestamp: int = Field(
        description="Unix timestamp of the event", example=1640995200000
    )
    message: Optional[MessengerMessageDto] = Field(
        None, description="Message content if this is a message event"
    )


class MessengerWebhookEntryDto(BaseModel):
    """Messenger webhook entry containing messaging events."""

    id: str = Field(description="Page ID", example="123456789012345")
    time: int = Field(description="Unix timestamp", example=1640995200000)
    messaging: List[MessengerWebhookEventDto] = Field(
        description="List of messaging events"
    )


class MessengerWebhookDto(BaseModel):
    """Complete messenger webhook payload."""

    object: str = Field(description="Type of webhook object", example="page")
    entry: List[MessengerWebhookEntryDto] = Field(description="List of webhook entries")


class WebhookVerificationDto(BaseModel):
    """Webhook verification parameters."""

    hub_mode: str = Field(
        alias="hub.mode", description="Webhook mode", example="subscribe"
    )
    hub_verify_token: str = Field(
        alias="hub.verify_token",
        description="Verification token",
        example="your_verify_token_here",
    )
    hub_challenge: str = Field(
        alias="hub.challenge",
        description="Challenge string to echo back",
        example="1234567890",
    )
