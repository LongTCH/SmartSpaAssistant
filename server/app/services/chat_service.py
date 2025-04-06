from starlette.responses import Response as HttpResponse
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from app.configs import env_config
import re

SENDER_ACTION = {
    "mark_seen": "mark_seen",
    "typing_on": "typing_on",
    "typing_off": "typing_off"
}

# Cấu trúc để lưu trữ tin nhắn đợi xử lý
map_message: Dict[str, Dict[str, Any]] = {}


async def process_message(sender_psid, webhook_event):
    """
    Process incoming messages and implements waiting logic
    """
    message = webhook_event.get("message")
    if message:
        text = message.get("text")
        attachments = message.get("attachments")

        # Xử lý postback ngay lập tức
        # if postback:
        #     await handle_chat(sender_psid, None, postback)
        #     return
        # Bỏ qua tin nhắn echo
        if message.get("is_echo", False):
            return

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

        # Tạo timer mới
        map_message[sender_psid]["timer"] = asyncio.create_task(
            process_after_wait(sender_psid, env_config.CHAT_WAIT_SECONDS))


async def process_after_wait(sender_psid, wait_seconds):
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
                await handle_chat(sender_psid, combined_message)

    except asyncio.CancelledError:
        # Timer đã bị hủy do có tin nhắn mới
        pass
    except Exception as e:
        print(f"Error in process_after_wait: {e}")


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

    combine_attachments = "\n".join(
        combine_attachments) if combine_attachments else ""

    # Gộp nhiều tin nhắn
    combined_message = combine_texts
    if combine_texts and combine_attachments:
        combined_message += f"\nDựa vào các file đính kèm:\n{combine_attachments}"

    return combined_message


async def send_action(sender_psid, action):
    url = f"https://graph.facebook.com/v22.0/{env_config.PAGE_ID}/messages"

    payload = {
        "recipient": {"id": sender_psid},
        "sender_action": action
    }

    params = {"access_token": env_config.PAGE_ACCESS_TOKEN}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, params=params):
            pass


async def keep_typing(sender_psid, stop_event):
    """
    Continuously sends typing_on indicator until stop_event is set
    """
    try:
        while not stop_event.is_set():
            await send_action(sender_psid, SENDER_ACTION["typing_on"])
            await asyncio.sleep(3)  # Send typing indicator every 3 seconds
    except Exception as e:
        print(f"Error in keep_typing: {e}")


async def handle_chat(sender_psid, message):
    if message:
        await send_action(sender_psid, SENDER_ACTION["mark_seen"])
        await asyncio.sleep(1)
        await send_action(sender_psid, SENDER_ACTION["typing_on"])

        # Create a stop event for the typing indicator
        stop_typing = asyncio.Event()

        # Start typing indicator in a background task
        typing_task = asyncio.create_task(
            keep_typing(sender_psid, stop_typing))

        # Handle the message
        # await handle_message(sender_psid, message)
        response_text = await send_to_n8n(sender_psid, message)
        message_parts = parse_and_format_message(response_text)
        for part in message_parts:
            if part.get("text"):
                response = {
                    "text": part["text"]
                }
            elif part.get("type"):
                response = {
                    "attachments": [{
                        "type": part["type"],
                        "payload": {
                            "url": part["url"],
                        }
                    }]
                }
            print(f"Response: {response}")
            await call_send_api(sender_psid, response)
            await asyncio.sleep(3)  # Delay between messages
        # Stop the typing indicator
        stop_typing.set()
        await typing_task


async def handle_message(sender_psid, received_message):
    """
    Handles messages events
    """
    response = {}

    # Checks if the message contains text
    if received_message.get("text"):
        # Create the payload for a basic text message
        response_text = await send_to_n8n(sender_psid, received_message.get("text"))
        response = {
            "text": response_text
        }
        await call_send_api(sender_psid, response)
    elif received_message.get("attachments"):
        # Xử lý nhiều ảnh nếu có
        attachments = received_message.get("attachments", [])

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


async def handle_postback(sender_psid, received_postback):
    """
    Handles messaging_postbacks events
    """
    # Get the payload for the postback
    payload = received_postback.get("payload")

    # Set the response based on the postback payload
    if payload == "yes":
        response = {"text": "Thanks!"}
    elif payload == "no":
        response = {"text": "Oops, try sending another image."}

    # Send the message to acknowledge the postback
    await call_send_api(sender_psid, response)


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
        "message": response
    }
    params = {"access_token": env_config.PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:  # ✅ Tự động đóng session
        async with session.post(url, json=payload, params=params, headers=headers) as response:
            pass


async def send_to_n8n(sender_psid, message):
    """
    Sends message to n8n webhook
    """
    payload = {
        "sender_psid": sender_psid,
        "message": message
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(env_config.N8N_MESSAGE_WEBHOOK_URL, json=payload) as response:
                if response.status == 200:
                    response_data = await response.text()
                    return response_data
                else:
                    return "Hiện tại em chưa thể trả lời được ạ. Em sẽ cố gắng trả lời sớm nhất có thể."
        except Exception as e:
            return "Hiện tại em chưa thể trả lời được ạ. Em sẽ cố gắng trả lời sớm nhất có thể."


def parse_and_format_message(message):
    # Define regex patterns for different types of links (image, video, file)
    media_patterns = {
        # Match image files
        "image": r'!\[.*?\]\((https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\)',
        # Match video files
        "video": r'!\[.*?\]\((https?://\S+\.(?:mp4|mov|avi|mkv|flv))\)',
        # Match file links
        "file": r'!\[.*?\]\((https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\)',
    }

    # If no media found, just return the text
    if not any(re.search(pattern, message) for pattern in media_patterns.values()):
        return [{"text": message.strip()}]
    
    # Replace bold text (**) with italic text (*)
    message = re.sub(r'\*\*(.*?)\*\*', r'*\1*', message)
    
    # Create a list to store media items with positions
    media_items = []
    
    # Create working copy of the message that we'll modify 
    working_message = message
    
    # Find all media occurrences with their positions
    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            full_match = match.group(0)  # The entire markdown syntax
            media_url = match.group(1)   # Just the URL part
            start_pos = match.start()
            end_pos = match.end()
            
            # Add to our media items list
            media_items.append({
                "type": media_type,
                "url": media_url,
                "start": start_pos,
                "end": end_pos,
                "full_match": full_match
            })
            
    # Sort media items by their position (from end to beginning to avoid position shifts)
    media_items.sort(key=lambda x: x["start"], reverse=True)
    
    # Replace all media markdown with placeholders in our working copy
    for i, item in enumerate(media_items):
        placeholder = f"__MEDIA_PLACEHOLDER_{i}__"
        working_message = working_message[:item["start"]] + placeholder + working_message[item["end"]:]
    
    # Split the modified message by placeholders
    parts = re.split(r'__MEDIA_PLACEHOLDER_\d+__', working_message)
    
    # Create the result with interleaved text and media
    result = []
    media_items.sort(key=lambda x: x["start"])  # Sort back to original order
    
    # Add text parts (filtered to remove empty ones) and media parts in correct order
    text_index = 0
    media_index = 0
    
    # Combine parts keeping track of original positions
    combined_parts = []
    
    # Add text parts first (removing empty ones)
    for i, text in enumerate(parts):
        if text and text.strip():
            # Find appropriate position
            start_pos = 0
            if i > 0 and media_index < len(media_items):
                start_pos = media_items[i-1]["end"]
            
            combined_parts.append({
                "type": "text",
                "content": text.strip(),
                "pos": start_pos
            })
    
    # Add media parts
    for item in media_items:
        combined_parts.append({
            "type": "media",
            "media_type": item["type"],
            "url": item["url"],
            "pos": item["start"]
        })
    
    # Sort all parts by their position
    combined_parts.sort(key=lambda x: x["pos"])
    
    # Convert to final output format
    for part in combined_parts:
        if part["type"] == "text":
            result.append({"text": part["content"]})
        else:
            result.append({"type": part["media_type"], "url": part["url"]})
            
    return result