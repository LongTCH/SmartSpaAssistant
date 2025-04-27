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
    message = WsMessageDto(
        message=WS_MESSAGES.INBOX, data=guest.to_dict(include=["interests"])
    )
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

            await save_message(
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
                await handle_chat(sender_psid, combined_message, guest)

    except asyncio.CancelledError as ex:
        # Timer đã bị hủy do có tin nhắn mới
        raise ex
    except Exception as e:
        print(f"Error in process_after_wait: {e}")


async def handle_chat(sender_psid, message, guest: Guest):
    """Handle chat with optional db session"""

    if message:
        try:
            await send_action(sender_psid, SENDER_ACTION["mark_seen"])

            # Start typing indicator in a background task
            typing_task = asyncio.create_task(keep_typing(sender_psid))

            # Handle the message
            response_text = await send_to_n8n(guest.id, message)

            message_parts = parse_and_format_message(response_text, 1000)

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
                await asyncio.sleep(2)

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
    await post_to_messenger(url, payload, params)


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
    """
    Chuyển đổi định dạng Markdown sang định dạng Messenger.
    """
    # Thêm một số ký tự đặc biệt vào văn bản để đánh dấu các định dạng
    # Thay thế **bold** thành <bold>bold</bold>
    text_after_bold = re.sub(r"\*\*(.*?)\*\*", r"<bold>\1</bold>", text)

    # Thay thế *italic* thành <italic>italic</italic>
    text_after_italic = re.sub(
        r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<italic>\1</italic>", text_after_bold
    )

    # Thay thế các dấu danh sách
    text_after_lists = re.sub(
        r"^\s*[\*\-]\s+", "• ", text_after_italic, flags=re.MULTILINE
    )

    # Sau khi đã xử lý xong các định dạng khác, chuyển đổi về định dạng Messenger
    # <bold>text</bold> -> *text*
    text_final_bold = re.sub(r"<bold>(.*?)</bold>", r"*\1*", text_after_lists)

    # <italic>text</italic> -> _text_
    text_final_italic = re.sub(r"<italic>(.*?)</italic>", r"_\1_", text_final_bold)

    # Xử lý các định dạng khác nếu cần
    final_text = re.sub(r"~~(.*?)~~", r"~\1~", text_final_italic)  # Gạch ngang

    return final_text


def messenger_to_markdown(text):
    """
    Chuyển đổi định dạng từ Messenger sang Markdown.
    """
    # Tương tự, sử dụng tags tạm thời để tránh xung đột

    # Thay thế *bold* thành <bold>bold</bold>
    text = re.sub(r"(?<!_)\*(?!_)(.*?)(?<!_)\*(?!_)", r"<bold>\1</bold>", text)

    # Thay thế _italic_ thành <italic>italic</italic>
    text = re.sub(r"_(.*?)_", r"<italic>\1</italic>", text)

    # Thay thế • thành dấu *
    text = re.sub(r"^\s*•\s+", "* ", text, flags=re.MULTILINE)

    # Chuyển đổi định dạng tạm về Markdown
    text = re.sub(r"<bold>(.*?)</bold>", r"**\1**", text)
    text = re.sub(r"<italic>(.*?)</italic>", r"*\1*", text)

    # Xử lý các định dạng khác
    text = re.sub(r"~(.*?)~", r"~~\1~~", text)  # Gạch ngang

    return text


def parse_and_format_message(message, char_limit=2000):
    """
    Parses and formats a message for Messenger, splitting it into multiple parts if it exceeds the character limit.

    Args:
        message: The message in markdown format to parse
        char_limit: The maximum number of characters allowed per message (default: 2000 for Messenger)

    Returns:
        A list of dictionaries containing either text or media parts
    """
    # Định nghĩa các mẫu regex cho các loại liên kết (hình ảnh, video, tệp)
    media_patterns = {
        "image": r"(?:!\[.*?\]\((https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))[^\)]*\))|(?:\[(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\])|(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))",
        "video": r"(?:!\[.*?\]\((https?://\S+?\.(?:mp4|mov|avi|mkv|flv))[^\)]*\))|(?:\[(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))\])|(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))",
        "file": r"(?:!\[.*?\]\((https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))[^\)]*\))|(?:\[(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\])|(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))",
    }

    # Tìm tất cả các media matches và vị trí của chúng
    all_matches = []
    extracted_urls = []  # Lưu trữ tất cả các URL đã trích xuất để loại bỏ trùng lặp

    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            # Xác định URL từ các nhóm match
            url = None
            if match.group(1):  # Trường hợp ![...](URL)
                url = match.group(1)
            elif match.group(2):  # Trường hợp [URL]
                url = match.group(2)
            elif match.group(3):  # Trường hợp URL trực tiếp
                url = match.group(3)
            else:
                url = match.group(0)

            # Làm sạch URL nếu còn bất kỳ dấu markdown nào
            if "](" in url:
                url = url.split("](")[-1]
            if "(" in url and ")" in url:
                url = url.split("(")[-1].split(")")[0]

            all_matches.append(
                {
                    "type": media_type,
                    "url": url,
                    "start": match.start(),
                    "end": match.end(),
                    "full_match": match.group(0),
                }
            )
            extracted_urls.append(url)

    # Nếu không tìm thấy media, chỉ trả về văn bản (có thể được chia nhỏ)
    if not all_matches:
        text_content = message.strip()
        # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
        # Thay thế [text](url) bằng url
        text_content = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_content)
        # Loại bỏ các link markdown còn sót lại mà không có text (ví dụ: [](url))
        text_content = re.sub(r"\[\]\((.*?)\)", r"\1", text_content)
        # Loại bỏ các URL đứng riêng trong ngoặc đơn nếu regex trên chưa bắt được
        text_content = re.sub(r"\((https?://[^)]+)\)", r"\1", text_content)

        # Chuyển đổi định dạng Markdown sang Messenger
        formatted_text = markdown_to_messenger(text_content)

        # Chia nhỏ nếu vượt quá giới hạn ký tự
        if len(formatted_text) <= char_limit:
            return [{"text": formatted_text}]
        else:
            return split_text_into_chunks(formatted_text, char_limit)

    # Sắp xếp các match theo vị trí
    all_matches.sort(key=lambda x: x["start"])

    # Loại bỏ các match trùng nhau hoặc chồng lấn
    filtered_matches = []
    for match in all_matches:
        # Kiểm tra xem URL đã tồn tại trong filtered_matches chưa
        if not any(match["url"] == existing["url"] for existing in filtered_matches):
            filtered_matches.append(match)

    # Chuyển đổi thành kết quả cuối cùng
    result = []
    current_pos = 0

    for match in filtered_matches:
        # Thêm text trước match
        if match["start"] > current_pos:
            text_before = message[current_pos : match["start"]].strip()
            if text_before:
                # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
                # Thay thế [text](url) bằng url
                text_before = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_before)
                # Loại bỏ các link markdown còn sót lại mà không có text (ví dụ: [](url))
                text_before = re.sub(r"\[\]\((.*?)\)", r"\1", text_before)
                # Loại bỏ các URL đứng riêng trong ngoặc đơn nếu regex trên chưa bắt được
                text_before = re.sub(r"\((https?://[^)]+)\)", r"\1", text_before)

                # Chuyển đổi định dạng Markdown sang Messenger
                text_before = markdown_to_messenger(text_before)

                # Chia nhỏ nếu vượt quá giới hạn ký tự
                if len(text_before) <= char_limit:
                    result.append({"text": text_before})
                else:
                    result.extend(split_text_into_chunks(text_before, char_limit))

        # Thêm media
        result.append({"type": match["type"], "url": match["url"]})
        current_pos = match["end"]

    # Thêm text còn lại sau match cuối cùng
    if current_pos < len(message):
        text_after = message[current_pos:].strip()
        if text_after:
            # Xử lý nội dung còn lại
            # Loại bỏ các URL đã được trích xuất thành media riêng để tránh trùng lặp
            for url in extracted_urls:
                text_after = text_after.replace(url, "")

            # Sửa định dạng MD sạch sẽ trước khi chuyển đổi
            # Trích xuất lại các danh sách và định dạng sạch sẽ
            lines = text_after.split("\n")
            clean_lines = []

            for line in lines:
                # Xử lý danh sách với dấu *
                if line.strip().startswith("*   **"):  # Danh sách lồng có đánh dấu đậm
                    # Sửa lại: Giữ nguyên định dạng in đậm cho tiêu đề phụ (không chuyển sang in nghiêng)
                    line = line.replace("*   **", "• **")
                elif line.strip().startswith("*   "):  # Danh sách thông thường
                    line = line.replace("*   ", "• ")

                # Thêm dòng đã sửa vào danh sách
                clean_lines.append(line)

            # Ghép các dòng lại
            text_after = "\n".join(clean_lines)

            # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
            text_after = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_after)
            text_after = re.sub(r"\[\]\((.*?)\)", r"\1", text_after)
            text_after = re.sub(r"\((https?://[^)]+)\)", r"\1", text_after)

            # Loại bỏ các dấu ngoặc rỗng
            # Loại bỏ dấu ngoặc đơn rỗng ()
            text_after = re.sub(r"\(\s*\)", "", text_after)
            # Loại bỏ dấu ngoặc vuông rỗng []
            text_after = re.sub(r"\[\s*\]", "", text_after)
            text_after = text_after.replace("()", "")

            # Chuyển đổi định dạng Markdown sang Messenger
            text_after = markdown_to_messenger(text_after)

            # Xử lý cuối cùng - làm sạch khoảng trắng thừa và định dạng lỗi
            # Sửa định dạng danh sách lồng nhau
            text_after = text_after.replace("* _", "• _")

            # Fix lỗi định dạng: chuyển lại các tiêu đề phụ từ in nghiêng sang in đậm
            # Tìm các mẫu như "• _Tẩy trang M32:_" và thay thế thành "• *Tẩy trang M32:*"
            text_after = re.sub(r"• _(.*?)(_\s)", r"• *\1*\2", text_after)
            text_after = re.sub(r"• _(.*?):_", r"• *\1:*", text_after)

            # Loại bỏ dòng trống thừa
            # Loại bỏ dòng trống thừa
            text_after = re.sub(r"\n\s+\n", "\n\n", text_after)
            # Giảm số dòng trống liên tiếp
            text_after = re.sub(r"\n{3,}", "\n\n", text_after)

            if (
                text_after.strip()
            ):  # Chỉ thêm vào kết quả nếu còn nội dung sau khi loại bỏ URL
                # Chia nhỏ nếu vượt quá giới hạn ký tự
                if len(text_after) <= char_limit:
                    result.append({"text": text_after})
                else:
                    result.extend(split_text_into_chunks(text_after, char_limit))

    return result


def split_text_into_chunks(text, char_limit=2000):
    """
    Chia văn bản thành các phần nhỏ hơn, theo thứ tự ưu tiên:
    1. Chia theo đoạn văn (dấu xuống dòng đôi)
    2. Chia theo dòng (dấu xuống dòng đơn)
    3. Chia theo câu (dấu chấm, chấm hỏi, chấm than)
    4. Chia theo từ nếu buộc phải chia giữa câu

    Args:
        text: Văn bản cần chia
        char_limit: Giới hạn ký tự mỗi phần (mặc định: 2000 cho Messenger)

    Returns:
        Một danh sách các dictionary, mỗi dictionary chứa một phần văn bản
    """
    result = []
    if len(text) <= char_limit:
        return [{"text": text}]

    # Phân tích văn bản để tìm các điểm chia phù hợp
    paragraphs = text.split("\n\n")  # Chia theo đoạn văn
    current_chunk = ""

    for paragraph in paragraphs:
        # Nếu đoạn văn tự nó đã vượt quá giới hạn
        if len(paragraph) > char_limit:
            # Nếu chunk hiện tại không rỗng, lưu lại
            if current_chunk:
                result.append({"text": current_chunk.strip()})
                current_chunk = ""

            # Xử lý đoạn văn dài, ưu tiên chia theo dòng
            lines = paragraph.split("\n")
            line_chunk = ""

            for line in lines:
                # Kiểm tra xem dòng có phải là gạch đầu dòng không
                is_bullet = line.strip().startswith("•") or line.strip().startswith("-")

                # Nếu thêm dòng mới vào vẫn trong giới hạn
                if (
                    len(line_chunk) + len(line) + 1 <= char_limit
                ):  # +1 cho ký tự xuống dòng
                    if line_chunk:
                        line_chunk += "\n" + line
                    else:
                        line_chunk = line
                else:
                    # Nếu dòng không phải gạch đầu dòng hoặc chunk hiện tại rỗng
                    if not is_bullet or not line_chunk:
                        # Lưu chunk hiện tại và bắt đầu chunk mới
                        if line_chunk:
                            result.append({"text": line_chunk.strip()})

                        # Nếu dòng hiện tại vẫn vượt quá giới hạn, cần chia nhỏ hơn nữa
                        if len(line) > char_limit:
                            # Thử chia theo câu nếu dòng quá dài
                            sentences = split_into_sentences(line)
                            sentence_chunk = ""

                            for sentence in sentences:
                                # Nếu câu đơn lẻ cũng vượt quá giới hạn
                                if len(sentence) > char_limit:
                                    # Nếu có chunk câu hiện tại, lưu lại
                                    if sentence_chunk:
                                        result.append({"text": sentence_chunk.strip()})
                                        sentence_chunk = ""

                                    # Chia câu theo từ
                                    parts = []
                                    words = sentence.split()
                                    part = ""
                                    for word in words:
                                        # +1 cho khoảng trắng
                                        if len(part) + len(word) + 1 <= char_limit:
                                            if part:
                                                part += " " + word
                                            else:
                                                part = word
                                        else:
                                            parts.append(part)
                                            part = word
                                    if part:
                                        parts.append(part)

                                    # Thêm các phần đã chia vào kết quả
                                    for part in parts:
                                        result.append({"text": part.strip()})

                                # Nếu câu vừa với giới hạn
                                elif len(sentence_chunk) + len(sentence) <= char_limit:
                                    sentence_chunk += sentence
                                else:
                                    # Lưu chunk câu hiện tại và bắt đầu chunk mới
                                    result.append({"text": sentence_chunk.strip()})
                                    sentence_chunk = sentence

                            # Lưu phần câu còn lại nếu có
                            if sentence_chunk:
                                result.append({"text": sentence_chunk.strip()})

                            line_chunk = ""
                        else:
                            line_chunk = line
                    else:
                        # Đối với gạch đầu dòng, giữ nguyên chunk hiện tại và thêm vào kết quả
                        result.append({"text": line_chunk.strip()})
                        line_chunk = line

            # Thêm phần còn lại của đoạn nếu có
            if line_chunk:
                result.append({"text": line_chunk.strip()})
        else:
            # Nếu thêm paragraph vào vẫn trong giới hạn
            if len(current_chunk) + len(paragraph) + 2 <= char_limit:  # +2 cho "\n\n"
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Lưu chunk hiện tại và bắt đầu chunk mới
                if current_chunk:
                    result.append({"text": current_chunk.strip()})
                current_chunk = paragraph

    # Thêm chunk cuối cùng nếu có
    if current_chunk:
        result.append({"text": current_chunk.strip()})

    return result


def split_into_sentences(text):
    """
    Chia văn bản thành các câu, sử dụng các dấu kết thúc câu chính
    và tránh chia các từ viết tắt hoặc số thập phân

    Args:
        text: Văn bản cần chia thành các câu

    Returns:
        Danh sách các câu
    """
    # Danh sách các dấu kết thúc câu
    sentence_endings = [".", "!", "?", ":", ";"]

    # Các ngoại lệ không chia (từ viết tắt, số thập phân, vv)
    exceptions = [
        "TS.",
        "GS.",
        "PGS.",
        "ThS.",
        "BS.",
        "BSCK.",
        "KS.",
        "CN.",
        "Dr.",
        "Mr.",
        "Mrs.",
        "TP.",
        "T.P",
        "Q.",
        "P.",
        "Tr.",
        "St.",
        "Tp.",
        "tp.",
        "Khu p.",
        "khu p.",
    ]

    sentences = []
    current = ""
    i = 0

    while i < len(text):
        current += text[i]

        # Kiểm tra xem ký tự hiện tại có phải là dấu kết thúc câu không
        if text[i] in sentence_endings:
            # Kiểm tra xem đây có phải là một ngoại lệ không
            is_exception = False
            for ex in exceptions:
                if current.endswith(ex) and (i + 1 >= len(text) or text[i + 1] == " "):
                    is_exception = True
                    break

            # Kiểm tra xem đây có phải là số thập phân không
            if (
                i > 0
                and i < len(text) - 1
                and text[i] == "."
                and text[i - 1].isdigit()
                and text[i + 1].isdigit()
            ):
                is_exception = True

            # Nếu không phải ngoại lệ và sau dấu câu là khoảng trắng hoặc hết chuỗi, kết thúc câu
            if not is_exception and (
                i + 1 >= len(text) or text[i + 1] == " " or text[i + 1] == "\n"
            ):
                sentences.append(current)
                current = ""

        i += 1

    # Thêm phần còn lại (nếu có)
    if current:
        sentences.append(current)

    return sentences
