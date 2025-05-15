import asyncio
import datetime
import os
from datetime import datetime
from typing import Any, Dict

import aiohttp
from app.baml_agents import invoke_agent
from app.configs import env_config
from app.configs.constants import CHAT_ASSIGNMENT, CHAT_SIDES, PROVIDERS
from app.configs.database import async_session
from app.models import Guest, GuestInfo
from app.repositories import guest_info_repository, guest_repository
from app.services import chat_service, interest_service
from app.stores.store import LOCAL_DATA
from app.utils.message_utils import (
    get_attachment_type_name,
    markdown_to_messenger,
    messenger_to_markdown,
    send_message_to_ws,
)
from baml_client.types import ChatResponseItem
from sqlalchemy.ext.asyncio import AsyncSession

SENDER_ACTION = {
    "mark_seen": "mark_seen",
    "typing_on": "typing_on",
    "typing_off": "typing_off",
}

# Cấu trúc để lưu trữ tin nhắn đợi xử lý
map_message: Dict[str, Dict[str, Any]] = {}


async def insert_guest(db: AsyncSession, sender_id) -> Guest | None:
    if not env_config.PAGE_ID or not env_config.PAGE_ACCESS_TOKEN:
        print("Missing PAGE_ID or PAGE_ACCESS_TOKEN")
        return
    # API endpoint
    url = f"https://graph.facebook.com/v22.0/{sender_id}"
    params = {
        "access_token": env_config.PAGE_ACCESS_TOKEN,
        "fields": "first_name,last_name,name,gender,picture",
    }
    image_url = f"https://graph.facebook.com/v22.0/{sender_id}/picture"
    image_params = {"access_token": env_config.PAGE_ACCESS_TOKEN, "type": "large"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                account_id = data.get("id")
                account_name = data.get("name")
                gender = data.get("gender")
                # Tải ảnh từ URL
                image_data = None
                async with session.get(
                    image_url, params=image_params
                ) as image_response:
                    if image_response.status != 200:
                        return {"error": "Không thể tải ảnh từ URL."}
                    image_data = await image_response.read()

                # Tạo Guest với provider và account_name trong guest
                guest = Guest(
                    provider=PROVIDERS.MESSENGER,
                    account_id=account_id,
                    account_name=account_name,
                    assigned_to=CHAT_ASSIGNMENT.AI,
                )
                guest = await guest_repository.insert_guest(db, guest)

                fullname = data.get("last_name") + " " + data.get("first_name")
                image_path = os.path.join("static", "images", f"{guest.id}.jpg")
                avatar_url = f"{env_config.BASE_URL}/static/images/{guest.id}.jpg"
                # Lưu ảnh vào thư mục 'images'
                with open(image_path, "wb") as f:
                    f.write(image_data)
                guest.avatar = avatar_url

                guest_info = GuestInfo(
                    fullname=fullname, gender=gender, guest_id=guest.id
                )

                # Lưu GuestInfo vào database
                guest_info = await guest_info_repository.insert_guest_info(
                    db, guest_info
                )

                await db.commit()
                return guest
            else:
                print(f"Error fetching user info: {response.status}")
                return None


async def process_message(sender_psid, receipient_psid, timestamp, webhook_event):
    """
    Process incoming messages and implements waiting logic
    """
    async with async_session() as db:
        try:
            message = webhook_event.get("message")
            if message:
                text = message.get("text")
                if text:
                    text = messenger_to_markdown(text)
                attachments = message.get("attachments")
                created_at = datetime.fromtimestamp(timestamp / 1000)

                if message.get("is_echo", False):
                    guest = await guest_repository.get_conversation_by_provider(
                        db, PROVIDERS.MESSENGER, receipient_psid
                    )
                    if guest:
                        # Convert millisecond timestamp to seconds for proper datetime handling
                        await chat_service.insert_chat(
                            db,
                            guest.id,
                            CHAT_SIDES.STAFF,
                            text,
                            attachments,
                            created_at,
                        )
                        guest = await guest_repository.get_guest_by_id(db, guest.id)
                        await send_message_to_ws(guest)
                    return

                # Ensure we explicitly handle the case when guest is None
                guest = await guest_repository.get_conversation_by_provider(
                    db, PROVIDERS.MESSENGER, sender_psid
                )
                if not guest:
                    guest = await insert_guest(db, sender_psid)
                    if not guest:
                        print(f"Failed to create guest for sender_psid: {sender_psid}")
                        return
                    await db.commit()

                await chat_service.insert_chat(
                    db, guest.id, CHAT_SIDES.CLIENT, text, attachments, created_at
                )
                guest = await guest_repository.get_guest_by_id(db, guest.id)
                await send_message_to_ws(guest)

                # Khởi tạo hoặc cập nhật thông tin tin nhắn cho người dùng
                if sender_psid not in map_message:
                    map_message[sender_psid] = {
                        "timer": None,
                        "texts": [],
                        "attachments": [],
                    }

                # Lưu tin nhắn mới
                if text:
                    map_message[sender_psid]["texts"].append(text)
                if attachments:
                    map_message[sender_psid]["attachments"].extend(attachments)

                # Hủy timer cũ nếu có
                if map_message[sender_psid]["timer"]:
                    map_message[sender_psid]["timer"].cancel()
                    map_message[sender_psid]["timer"] = None

                # Tạo timer mới với db session được truyền vào
                map_message[sender_psid]["timer"] = asyncio.create_task(
                    process_after_wait(sender_psid, LOCAL_DATA.chat_wait_seconds, guest)
                )
        except Exception as e:
            print(f"Error in process_message: {e}")


async def process_after_wait(sender_psid, wait_seconds: float, guest: Guest):
    """
    Đợi một khoảng thời gian rồi xử lý tin nhắn tích lũy
    """
    async with async_session() as db:
        try:
            await asyncio.sleep(wait_seconds)

            # Lấy dữ liệu người dùng
            if sender_psid in map_message:
                user_data = map_message[sender_psid]

                # Lấy tin nhắn đã tích lũy
                texts = user_data["texts"]
                attachments = user_data["attachments"]

                # Xóa dữ liệu người dùng
                del map_message[sender_psid]

                # Gộp tin nhắn
                combined_message = combine_messages(texts, attachments)

                # Xử lý tin nhắn
                if combined_message:
                    # sentiment, should_reset = await sentiment_service.analyze_sentiment(
                    #     db, guest
                    # )
                    # if sentiment != guest.sentiment:
                    #     guest.sentiment = sentiment
                    #     await sentiment_service.update_sentiment_to_websocket(guest)
                    #     await guest_repository.update_sentiment(db, guest.id, sentiment)
                    # if should_reset:
                    #     await guest_repository.reset_message_count(db, guest.id)
                    # Process interests
                    interest_ids = await interest_service.get_interest_ids_from_text(
                        db, combined_message
                    )
                    await guest_repository.add_interests_to_guest_by_id(
                        db, guest.id, interest_ids
                    )
                    # Handle the chat message
                    await handle_chat(sender_psid, combined_message, guest)
                    await db.commit()
        except asyncio.CancelledError as ex:
            await db.rollback()
            raise ex
        except Exception as e:
            await db.rollback()
            print(f"Error in process_after_wait: {e}")


async def handle_chat(sender_psid, message, guest: Guest):
    """Handle chat with optional db session"""

    if message:
        try:
            await send_action(sender_psid, SENDER_ACTION["mark_seen"])

            # Start typing indicator in a background task
            typing_task = asyncio.create_task(keep_typing(sender_psid))

            # Handle the message
            message_parts: list[ChatResponseItem] = await invoke_agent(
                guest.id, message
            )

            for part in message_parts:
                if part.type == "text":
                    part.payload = markdown_to_messenger(part.payload)

            for part in message_parts:
                if part.type == "text" or part.type == "link":
                    response = {"text": part.payload}
                else:
                    response = {
                        "attachments": [
                            {
                                "type": part.type,
                                "payload": {
                                    "url": part.payload,
                                },
                            }
                        ]
                    }
                await call_send_api(sender_psid, response)
                await asyncio.sleep(2)

        except Exception as e:
            print(f"Error in handle_chat: {e}")
            raise e
        finally:
            if typing_task:
                typing_task.cancel()


def combine_messages(texts, attachments):
    """
    Gộp nhiều tin nhắn thành một tin nhắn tổng hợp
    """
    if not texts and not attachments:
        return None
    combine_texts = "\n".join(texts) if texts else ""

    combine_attachments = []
    for attachment in attachments:
        attachment_type = get_attachment_type_name(attachment)
        attachment_url = attachment.get("payload", {}).get("url")
        if attachment_url:
            combine_attachments.append(f"{attachment_type}: {attachment_url}")
        # else:
        #     combine_attachments.append(f"{attachment_type}: {attachment}")

    combine_attachments = "\n".join(combine_attachments) if combine_attachments else ""

    # Gộp nhiều tin nhắn
    combined_message = combine_texts
    if combine_texts and combine_attachments:
        combined_message += f"\nDựa vào các file đính kèm:\n{combine_attachments}"

    return combined_message


async def send_action(sender_psid, action):
    url = f"https://graph.facebook.com/v22.0/{env_config.PAGE_ID}/messages"

    payload = {"recipient": {"id": sender_psid}, "sender_action": action}

    params = {"access_token": env_config.PAGE_ACCESS_TOKEN}
    await post_to_messenger(url, payload, params)


async def keep_typing(sender_psid):
    """
    Continuously sends typing_on indicator
    """
    try:
        while True:
            await send_action(sender_psid, SENDER_ACTION["typing_on"])
            await asyncio.sleep(5)  # Send typing indicator every 5 seconds
    except Exception as e:
        print(f"Error in keep_typing: {e}")


async def handle_message(sender_psid, received_message):
    """
    Handles messages events
    """
    response = {}

    # Checks if the message contains text
    if received_message.get("text"):
        # Create the payload for a basic text message
        response_text = await send_to_n8n(sender_psid, received_message.get("text"))
        response = {"text": response_text}
        await call_send_api(sender_psid, response)
    elif received_message.get("attachments"):
        # Xử lý nhiều ảnh nếu có
        received_message.get("attachments", [])

        # Nếu chỉ có một ảnh, xử lý như cũ
        # if len(attachments) == 1:
        #     attachment_url = attachments[0].get("payload", {}).get("url")
        #     response = {
        #         "attachment": {
        #             "type": "template",
        #             "payload": {
        #                 "template_type": "generic",
        #                 "elements": [{
        #                     "title": "Is this the right picture?",
        #                     "subtitle": "Tap a button to answer.",
        #                     "image_url": attachment_url,
        #                     "buttons": [
        #                         {
        #                             "type": "postback",
        #                             "title": "Yes!",
        #                             "payload": "yes",
        #                         },
        #                         {
        #                             "type": "postback",
        #                             "title": "No!",
        #                             "payload": "no",
        #                         }
        #                     ],
        #                 }]
        #             }
        #         }
        #     }
        #     await call_send_api(sender_psid, response)
        # else:
        #     # Xử lý nhiều ảnh
        #     response = {
        #         "text": f"Tôi đã nhận được {len(attachments)} ảnh từ bạn."
        #     }
        #     await call_send_api(sender_psid, response)


async def call_send_api(sender_psid, response) -> bool:
    """
    Sends response messages via the Send API (Graph API v22.0)

    Args:
        sender_psid: The recipient ID
        response: The message response to send

    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    # No need to send typing_off here as it will be handled by the main task
    if not env_config.PAGE_ID or not env_config.PAGE_ACCESS_TOKEN:
        print("Missing PAGE_ID or PAGE_ACCESS_TOKEN")
        return False

    # API endpoint
    url = f"https://graph.facebook.com/v22.0/{env_config.PAGE_ID}/messages"

    # JSON payload
    payload = {
        "recipient": {"id": sender_psid},
        "messaging_type": "RESPONSE",
        "message": response,
    }
    params = {"access_token": env_config.PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}

    # Send the message and return the result
    return await post_to_messenger(url, payload, params, headers)


async def post_to_messenger(url, payload, params, headers=None, retry=5) -> bool:
    """
    Sends a POST request to the Messenger API with retry logic.
    Returns True if the request was successful, False otherwise.

    Args:
        url: The URL to send the request to
        payload: The JSON payload to send
        params: URL parameters
        headers: HTTP headers (can be None)
        retry: Number of retry attempts (default: 5)

    Returns:
        bool: True if successful, False if all retries failed
    """
    attempt = 0
    # Set default headers if None
    if headers is None:
        headers = {"Content-Type": "application/json"}

    while attempt < retry:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, params=params, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(
                            f"Request failed with status {response.status}, attempt {attempt + 1}/{retry}"
                        )
                        attempt += 1
                        if attempt < retry:
                            # Exponential backoff: wait 2^attempt seconds before retrying
                            await asyncio.sleep(2**attempt)
                        else:
                            print(f"All {retry} attempts failed for request to {url}")
                            return False
        except Exception as e:
            print(f"Error during request: {e}, attempt {attempt + 1}/{retry}")
            attempt += 1
            if attempt < retry:
                # Exponential backoff: wait 2^attempt seconds before retrying
                await asyncio.sleep(2**attempt)
            else:
                print(
                    f"All {retry} attempts failed for request to {url} due to exception: {e}"
                )
                return False

    return False


async def send_to_n8n(sender_psid, message):
    """
    Sends message to n8n webhook
    """
    payload = {"sender_psid": sender_psid, "message": message}

    async with aiohttp.ClientSession() as session:
        # Send the message to n8n webhook
        async with session.post(
            env_config.N8N_MESSAGE_WEBHOOK_URL, json=payload
        ) as response:
            if response.status == 200:
                response_data = await response.text()
                return response_data
            else:
                print(f"Error: {response.status}")
                return "Hiện tại em chưa thể trả lời được ạ. Em sẽ cố gắng trả lời sớm nhất có thể."
