import json
from typing import Any, Dict

from app.stores import store
from app.stores.store import LocalData, read_json_file

LOCAL_DATA_PATH = "./app/stores/localData.json"


async def get_local_data() -> LocalData:
    """
    Lấy dữ liệu cấu hình local dưới dạng đối tượng LocalData.

    Returns:
        LocalData: Đối tượng cấu hình local data
    """
    return store.LOCAL_DATA


async def get_local_data_dict() -> Dict[str, Any]:
    """
    Lấy dữ liệu cấu hình local dưới dạng dictionary.

    Returns:
        Dict[str, Any]: Dữ liệu cấu hình local
    """
    with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


async def save_local_data(data: Dict[str, Any]) -> LocalData:
    """
    Lưu dữ liệu cấu hình local và cập nhật đối tượng LOCAL_DATA toàn cục.

    Args:
        data (Dict[str, Any]): Dữ liệu cấu hình để lưu

    Returns:
        LocalData: Đối tượng cấu hình local data đã cập nhật
    """
    # Ghi dữ liệu vào file
    with open(LOCAL_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    # Cập nhật đối tượng LOCAL_DATA toàn cục và trả về
    store.LOCAL_DATA = read_json_file(LOCAL_DATA_PATH)
    return store.LOCAL_DATA


async def update_local_data(updates: Dict[str, Any]) -> LocalData:
    """
    Cập nhật từng thuộc tính cụ thể trong dữ liệu cấu hình local.

    Hàm này chỉ cập nhật các trường được chỉ định trong updates,
    giữ nguyên các trường khác.

    Args:
        updates (Dict[str, Any]): Dictionary chứa các thuộc tính cần cập nhật

    Returns:
        LocalData: Đối tượng cấu hình local data đã cập nhật
    """
    # Lấy dữ liệu hiện tại
    current_data = await get_local_data_dict()

    # Cập nhật các trường đơn giản
    if "DRIVE_FOLDER_ID" in updates:
        current_data["DRIVE_FOLDER_ID"] = updates["DRIVE_FOLDER_ID"]
    if "CHAT_WAIT_SECONDS" in updates:
        current_data["CHAT_WAIT_SECONDS"] = updates["CHAT_WAIT_SECONDS"]
    if "SENTIMENT_INTERVAL_CHAT_COUNT" in updates:
        current_data["SENTIMENT_INTERVAL_CHAT_COUNT"] = updates[
            "SENTIMENT_INTERVAL_CHAT_COUNT"
        ]
    if "REACTION_MESSAGE" in updates:
        current_data["REACTION_MESSAGE"] = updates["REACTION_MESSAGE"]

    # Cập nhật đối tượng lồng nhau FORM_OF_ADDRESS
    if "FORM_OF_ADDRESS" in updates:
        form_updates = updates["FORM_OF_ADDRESS"]
        if not isinstance(current_data.get("FORM_OF_ADDRESS"), dict):
            current_data["FORM_OF_ADDRESS"] = {}

        if "ME" in form_updates:
            current_data["FORM_OF_ADDRESS"]["ME"] = form_updates["ME"]
        if "OTHER" in form_updates:
            current_data["FORM_OF_ADDRESS"]["OTHER"] = form_updates["OTHER"]

    # Cập nhật đối tượng lồng nhau UNDEFINED_MESSAGE_HANDLER
    if "UNDEFINED_MESSAGE_HANDLER" in updates:
        handler_updates = updates["UNDEFINED_MESSAGE_HANDLER"]
        if not isinstance(current_data.get("UNDEFINED_MESSAGE_HANDLER"), dict):
            current_data["UNDEFINED_MESSAGE_HANDLER"] = {}

        if "TYPE" in handler_updates:
            current_data["UNDEFINED_MESSAGE_HANDLER"]["TYPE"] = handler_updates["TYPE"]
        if "MESSAGE" in handler_updates:
            current_data["UNDEFINED_MESSAGE_HANDLER"]["MESSAGE"] = handler_updates[
                "MESSAGE"
            ]

    # Lưu dữ liệu đã cập nhật
    return await save_local_data(current_data)
