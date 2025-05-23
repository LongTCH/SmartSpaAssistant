import json
from typing import Optional

from pydantic import BaseModel


class LocalData(BaseModel):
    chat_wait_seconds: Optional[float] = None
    max_script_retrieval: Optional[int] = None  # Added
    reaction_message: Optional[str] = None
    identity: Optional[str] = None
    instructions: Optional[str] = None


# Đọc dữ liệu từ file JSON
def read_json_file(file_path: str) -> LocalData:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

        # Create and return LocalData object using Pydantic
        return LocalData(
            chat_wait_seconds=float(data["CHAT_WAIT_SECONDS"]),
            max_script_retrieval=int(data["MAX_SCRIPT_RETRIEVAL"]),
            reaction_message=data["REACTION_MESSAGE"],
            identity=data["IDENTITY"],
            instructions=data["INSTRUCTIONS"],
        )


file_path = "./app/stores/localData.json"


def get_local_data() -> LocalData:
    """
    Trả về dữ liệu cục bộ từ file JSON.
    """
    return read_json_file(file_path)
