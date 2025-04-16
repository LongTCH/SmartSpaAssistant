import json

from app.dtos import LocalData


# Đọc dữ liệu từ file JSON
def read_json_file(file_path: str) -> LocalData:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return LocalData(
            drive_folder_id=data.get("DRIVE_FOLDER_ID", ""),
            chat_wait_seconds=float(data.get("CHAT_WAIT_SECONDS", 0)),
            sentiment_interval_chat_count=int(
                data.get("SENTIMENT_INTERVAL_CHAT_COUNT", 0)
            ),
        )


# Sử dụng
file_path = "./app/stores/localData.json"
LOCAL_DATA = read_json_file(file_path)
