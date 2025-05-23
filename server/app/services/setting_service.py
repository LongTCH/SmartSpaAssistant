import json
from typing import Any, Dict

from app.stores.store import LocalData
from app.stores.store import get_local_data as get_local_data_from_store

LOCAL_DATA_PATH = "./app/stores/localData.json"


async def get_local_data() -> LocalData:
    """
    Lấy dữ liệu cấu hình local dưới dạng đối tượng LocalData.
    Luôn load lại từ file để đảm bảo dữ liệu mới nhất.

    Returns:
        LocalData: Đối tượng cấu hình local data
    """
    return get_local_data_from_store()


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
    Lưu dữ liệu cấu hình local.

    Args:
        data (Dict[str, Any]): Dữ liệu cấu hình để lưu

    Returns:
        LocalData: Đối tượng cấu hình local data đã cập nhật
    """
    # Ghi dữ liệu vào file
    with open(LOCAL_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    # Trả về đối tượng LocalData mới được load từ file
    return get_local_data_from_store()


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
    if "CHAT_WAIT_SECONDS" in updates:
        current_data["CHAT_WAIT_SECONDS"] = updates["CHAT_WAIT_SECONDS"]

    if "MAX_SCRIPT_RETRIEVAL" in updates:
        current_data["MAX_SCRIPT_RETRIEVAL"] = updates["MAX_SCRIPT_RETRIEVAL"]

    if "REACTION_MESSAGE" in updates:
        current_data["REACTION_MESSAGE"] = updates["REACTION_MESSAGE"]

    if "IDENTITY" in updates:
        current_data["IDENTITY"] = updates["IDENTITY"]

    if "INSTRUCTIONS" in updates:
        current_data["INSTRUCTIONS"] = updates["INSTRUCTIONS"]

    # Lưu dữ liệu đã cập nhật
    return await save_local_data(current_data)
