import asyncio
import datetime
import os
import re
from datetime import datetime
from typing import Any, Dict

import aiohttp
import requests
from app.configs import env_config
from app.configs.constants import CHAT_ASSIGNMENT, CHAT_SIDES, PROVIDERS, WS_MESSAGES
from app.configs.database import process_background_with_session
from app.dtos import WsMessageDto
from app.models import Chat, Guest, GuestInfo
from app.repositories import chat_repository, guest_info_repository, guest_repository
from app.services import interest_service
from app.services.connection_manager import manager
from app.services.integrations import sentiment_service
from app.stores.store import LOCAL_DATA
from sqlalchemy.ext.asyncio import AsyncSession

SENDER_ACTION = {
    "mark_seen": "mark_seen",
    "typing_on": "typing_on",
    "typing_off": "typing_off",
}

# Cấu trúc để lưu trữ tin nhắn đợi xử lý
map_message: Dict[str, Dict[str, Any]] = {}


async def save_message(
    db: AsyncSession,
    guest_id: str,
    side: str,
    text: str,
    attachments: list,
    created_at: datetime,
):
    """
    Lưu tin nhắn vào cơ sở dữ liệu hoặc bộ nhớ tạm thời
    """
    message = {"text": text, "attachments": attachments}
    content = {"side": side, "message": message}
    chat = Chat(guest_id=guest_id, content=content, created_at=created_at)
    await chat_repository.insert_chat(db, chat)
    # increase message count
    await guest_repository.increase_message_count(db, guest_id)
    # update last message
    guest = await guest_repository.update_last_message(
        db, guest_id, chat.content, chat.created_at
    )
    await db.commit()
    await db.refresh(guest)
    return guest


async def get_conversation(db: AsyncSession, sender_psid):
    """
    Lấy thông tin cuộc trò chuyện từ cơ sở dữ liệu hoặc bộ nhớ tạm thời
    """
    return await guest_repository.get_conversation_by_provider(
        db, PROVIDERS.MESSENGER, sender_psid
    )


async def insert_guest(db: AsyncSession, sender_id):
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
                image_response = requests.get(image_url, params=image_params)
                if image_response.status_code != 200:
                    return {"error": "Không thể tải ảnh từ URL."}

                fullname = data.get("last_name") + " " + data.get("first_name")

                # Tạo GuestInfo trước - không có provider và account_name
                guest_info = GuestInfo(fullname=fullname, gender=gender)

                # Lưu GuestInfo vào database
                guest_info = await guest_info_repository.insert_guest_info(
                    db, guest_info
                )

                # Tạo Guest với provider và account_name trong guest
                guest = Guest(
                    provider=PROVIDERS.MESSENGER,
                    account_id=account_id,
                    account_name=account_name,
                    info_id=guest_info.id,
                    assigned_to=CHAT_ASSIGNMENT.AI,
                )
                guest = await guest_repository.insert_guest(db, guest)

                image_path = os.path.join("static", "images", f"{guest.id}.jpg")
                avatar_url = f"{env_config.BASE_URL}/static/images/{guest.id}.jpg"
                # Lưu ảnh vào thư mục 'images'
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                guest.avatar = avatar_url
                await db.commit()
                return guest
            else:
                print(f"Error fetching user info: {response.status}")
                return None


async def send_message_to_ws(guest: Guest):
    """
    Gửi tin nhắn đến WebSocket
    """
    message = WsMessageDto(message=WS_MESSAGES.INBOX, data=guest.to_dict())
    await manager.broadcast(message)


# Replace process_message with this fixed version:


async def process_message(
    db: AsyncSession, sender_psid, receipient_psid, timestamp, webhook_event
):
    """
    Process incoming messages and implements waiting logic
    """
    try:
        message = webhook_event.get("message")
        if message:
            text = message.get("text")
            if text:
                text = messenger_to_markdown(text)
            attachments = message.get("attachments")
            created_at = datetime.fromtimestamp(timestamp / 1000)

            if message.get("is_echo", False):
                guest = await get_conversation(db, receipient_psid)
                if guest:
                    # Convert millisecond timestamp to seconds for proper datetime handling
                    guest = await save_message(
                        db, guest.id, CHAT_SIDES.STAFF, text, attachments, created_at
                    )
                    await send_message_to_ws(guest)
                return

            # Ensure we explicitly handle the case when guest is None
            guest = await get_conversation(db, sender_psid)
            if not guest:
                guest = await insert_guest(db, sender_psid)
                if not guest:
                    print(f"Failed to create guest for sender_psid: {sender_psid}")
                    return

            guest = await save_message(
                db, guest.id, CHAT_SIDES.CLIENT, text, attachments, created_at
            )
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
                process_background_with_session(
                    process_after_wait, sender_psid, LOCAL_DATA.chat_wait_seconds, guest
                )
            )
    except Exception as e:
        print(f"Error in process_message: {e}")
        # Don't close the session here, it's managed by the caller


async def process_after_wait(
    db: AsyncSession, sender_psid, wait_seconds: float, guest: Guest
):
    """
    Đợi một khoảng thời gian rồi xử lý tin nhắn tích lũy
    """
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
                sentiment, should_reset = await sentiment_service.analyze_sentiment(
                    db, guest
                )
                if sentiment != guest.sentiment:
                    guest.sentiment = sentiment
                    await sentiment_service.update_sentiment_to_websocket(guest)
                    await guest_repository.update_sentiment(db, guest.id, sentiment)
                if should_reset:
                    await guest_repository.reset_message_count(db, guest.id)
                # Process interests
                interest_ids = await interest_service.get_interest_ids_from_text(
                    db, combined_message
                )
                await guest_repository.add_interests_to_guest_by_id(
                    db, guest.id, interest_ids
                )
                # Handle the chat message
                await handle_chat(sender_psid, combined_message, db)

    except asyncio.CancelledError as ex:
        # Timer đã bị hủy do có tin nhắn mới
        raise ex
    except Exception as e:
        print(f"Error in process_after_wait: {e}")


async def handle_chat(sender_psid, message, db: AsyncSession = None):
    """Handle chat with optional db session"""

    if message:
        try:
            await send_action(sender_psid, SENDER_ACTION["mark_seen"])

            # Start typing indicator in a background task
            typing_task = asyncio.create_task(keep_typing(sender_psid))

            # Handle the message
            response_text = await send_to_n8n(sender_psid, message)

            message_parts = parse_and_format_message(response_text)

            for part in message_parts:
                if part.get("text"):
                    response = {"text": part["text"]}
                elif part.get("type"):
                    response = {
                        "attachments": [
                            {
                                "type": part["type"],
                                "payload": {
                                    "url": part["url"],
                                },
                            }
                        ]
                    }
                await call_send_api(sender_psid, response)
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in handle_chat: {e}")
            raise e
        finally:
            if typing_task:
                typing_task.cancel()


def get_attachment_type_name(attachment):
    """
    Lấy tên loại tệp đính kèm
    """
    if attachment["type"] == "image":
        return "Hình ảnh"
    elif attachment["type"] == "video":
        return "Video"
    elif attachment["type"] == "audio":
        return "Âm thanh"
    elif attachment["type"] == "file":
        return "Tệp tin"
    elif attachment["type"] == "location":
        return "Vị trí"
    elif attachment["type"] == "template":
        return "Mẫu"


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

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, params=params):
            pass


async def keep_typing(sender_psid):
    """
    Continuously sends typing_on indicator
    """
    try:
        while True:
            await send_action(sender_psid, SENDER_ACTION["typing_on"])
            await asyncio.sleep(3)  # Send typing indicator every 3 seconds
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


async def call_send_api(sender_psid, response):
    """
    Sends response messages via the Send API (Graph API v22.0)
    """
    # No need to send typing_off here as it will be handled by the main task
    if not env_config.PAGE_ID or not env_config.PAGE_ACCESS_TOKEN:
        print("Missing PAGE_ID or PAGE_ACCESS_TOKEN")
        return
    # API endpoint
    url = f"https://graph.facebook.com/v22.0/{env_config.PAGE_ID}/messages"

    # JSON payload (đúng chuẩn)
    payload = {
        "recipient": {"id": sender_psid},
        "messaging_type": "RESPONSE",
        "message": response,
    }
    params = {"access_token": env_config.PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:  # ✅ Tự động đóng session
        async with session.post(
            url, json=payload, params=params, headers=headers
        ) as response:
            pass


async def send_to_n8n(sender_psid, message):
    """
    Sends message to n8n webhook
    """
    payload = {"sender_psid": sender_psid, "message": message}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                env_config.N8N_MESSAGE_WEBHOOK_URL, json=payload
            ) as response:
                if response.status == 200:
                    response_data = await response.text()
                    return response_data
                else:
                    return "Hiện tại em chưa thể trả lời được ạ. Em sẽ cố gắng trả lời sớm nhất có thể."
        except Exception as e:
            return "Hiện tại em chưa thể trả lời được ạ. Em sẽ cố gắng trả lời sớm nhất có thể."


def markdown_to_messenger(text):
    # In đậm: **bold** → *bold*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    # In nghiêng: *italic* → _italic_
    text = re.sub(r"\*(.*?)\*", r"_\1_", text)
    # Gạch ngang: ~~strikethrough~~ → ~strikethrough~
    text = re.sub(r"~~(.*?)~~", r"~\1~", text)
    # Mã nguồn: `code` → `code`
    text = re.sub(r"`(.*?)`", r"`\1`", text)
    # Khối mã: ```code``` → ```code```
    text = re.sub(r"```(.*?)```", r"``` \1 ```", text, flags=re.DOTALL)
    # Liên kết: [text](url) → [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"[\1](\2)", text)
    return text


def messenger_to_markdown(text):
    # In đậm: *bold* → **bold**
    text = re.sub(r"\*(.*?)\*", r"**\1**", text)
    # In nghiêng: _italic_ → *italic*
    text = re.sub(r"_(.*?)_", r"*\1*", text)
    # Gạch ngang: ~strikethrough~ → ~~strikethrough~~
    text = re.sub(r"~(.*?)~", r"~~\1~~", text)
    # Mã nguồn: `code` → `code`
    text = re.sub(r"`(.*?)`", r"`\1`", text)
    # Khối mã: ```code``` → ```code```
    text = re.sub(r"```(.*?)```", r"``` \1 ```", text, flags=re.DOTALL)
    # Liên kết: [text](url) → [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"[\1](\2)", text)
    return text


def parse_and_format_message(message):
    # Định nghĩa các mẫu regex cho các loại liên kết (hình ảnh, video, tệp)
    media_patterns = {
        "image": r"!\[.*?\]\((https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\)|(https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))",
        "video": r"!\[.*?\]\((https?://\S+\.(?:mp4|mov|avi|mkv|flv))\)|(https?://\S+\.(?:mp4|mov|avi|mkv|flv))",
        "file": r"!\[.*?\]\((https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\)|(https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))",
    }

    # Nếu không tìm thấy media, chỉ trả về văn bản
    if not any(re.search(pattern, message) for pattern in media_patterns.values()):
        return [{"text": message.strip()}]

    message = markdown_to_messenger(message)

    # Danh sách chứa các phần media với vị trí
    media_items = []

    # Tạo bản sao làm việc của tin nhắn để chỉnh sửa
    working_message = message

    # Tìm tất cả các media với vị trí của chúng
    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            full_match = match.group(0)
            # Xử lý cả hai trường hợp: URL trong markdown và URL trực tiếp
            if len(match.groups()) >= 1 and match.group(1):
                media_url = match.group(1)  # URL trong markdown ![...](URL)
            elif len(match.groups()) >= 2 and match.group(2):
                media_url = match.group(2)  # URL trực tiếp
            else:
                media_url = full_match  # Fallback đến toàn bộ match

            start_pos = match.start()
            end_pos = match.end()

            media_items.append(
                {
                    "type": media_type,
                    "url": media_url,
                    "start": start_pos,
                    "end": end_pos,
                    "full_match": full_match,
                }
            )

    # Sắp xếp các phần media theo vị trí (từ cuối đến đầu để tránh thay đổi vị trí)
    media_items.sort(key=lambda x: x["start"], reverse=True)

    # Thay thế tất cả các markdown media bằng placeholder trong bản sao làm việc
    for i, item in enumerate(media_items):
        placeholder = f"__MEDIA_PLACEHOLDER_{i}__"
        working_message = (
            working_message[: item["start"]]
            + placeholder
            + working_message[item["end"] :]
        )

    # Tách tin nhắn đã chỉnh sửa theo các placeholder
    parts = re.split(r"__MEDIA_PLACEHOLDER_\d+__", working_message)

    # Tạo kết quả với văn bản và media xen kẽ
    result = []
    media_items.sort(key=lambda x: x["start"])

    media_index = 0
    combined_parts = []

    for i, text in enumerate(parts):
        if text and text.strip():
            start_pos = 0
            if i > 0 and media_index < len(media_items):
                start_pos = media_items[i - 1]["end"]

            combined_parts.append(
                {"type": "text", "content": text.strip(), "pos": start_pos}
            )

    for item in media_items:
        combined_parts.append(
            {
                "type": "media",
                "media_type": item["type"],
                "url": item["url"],
                "pos": item["start"],
            }
        )

    combined_parts.sort(key=lambda x: x["pos"])

    for part in combined_parts:
        if part["type"] == "text":
            result.append({"text": part["content"]})
        else:
            result.append({"type": part["media_type"], "url": part["url"]})

    return result
