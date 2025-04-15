import requests
from app.configs import env_config
from app.repositories import guest_repository, chat_repository
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Guest
from app.stores.store import LOCAL_DATA
from app.services.connection_manager import manager
from app.configs.constants import WS_MESSAGES
from app.dtos import WsMessageDto


async def update_sentiment_to_websocket(guest: Guest) -> None:
    """
    Update the sentiment of the guest in the WebSocket connection.
    """
    message = WsMessageDto(message=WS_MESSAGES.UPDATE_SENTIMENT,
                           data=guest.to_dict())
    await manager.broadcast(message)


async def analyze_sentiment(db: AsyncSession, guest: Guest) -> str:
    """
    Analyze the sentiment of the given text using a sentiment analysis API.
    """
    sentiment = "neutral"
    url = env_config.N8N_SENTIMENT_WEBHOOK_URL
    message_count = guest.message_count
    old_sentiment = guest.sentiment

    if message_count >= LOCAL_DATA.sentiment_interval_chat_count:
        chat_histories = await chat_repository.get_chat_by_guest_id(
            db, guest.id, 0, message_count)

        # Filter out chats with empty text
        filtered_chats = [
            chat for chat in chat_histories
            if chat.content.get("message") and
            chat.content["message"].get("text") and
            chat.content["message"]["text"].strip()
        ]

        payload = {"chats": [chat.to_dict() for chat in filtered_chats]}
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            sentiment = response.json().get("sentiment", "neutral")
        if sentiment != old_sentiment:
            guest.sentiment = sentiment
            await update_sentiment_to_websocket(guest)
            await guest_repository.update_sentiment(
                db, guest.id, sentiment)
        await guest_repository.reset_message_count(db, guest.id)
        await db.commit()

    return sentiment
