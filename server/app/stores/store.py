import json
from app.dtos import LocalData


# Đọc dữ liệu từ file JSON
def read_json_file(file_path: str) -> LocalData:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return LocalData(
            drive_folder_id=data.get("DRIVE_FOLDER_ID", "")
        )


# Sử dụng
file_path = './app/stores/localData.json'
LOCAL_DATA = read_json_file(file_path)
