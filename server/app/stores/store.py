import json
from enum import Enum


class LocalData:
    def __init__(
        self,
        drive_folder_id: str = None,
        chat_wait_seconds: float = None,
        sentiment_interval_chat_count: int = None,
        form_of_address: "LocalData.FormOfAddress" = None,
        reaction_message: str = None,
        undefined_message_handler: "LocalData.UndefinedMessageHandler" = None,
    ):
        self.drive_folder_id = drive_folder_id
        self.chat_wait_seconds = chat_wait_seconds
        self.sentiment_interval_chat_count = sentiment_interval_chat_count
        self.form_of_address = form_of_address
        self.reaction_message = reaction_message
        self.undefined_message_handler = undefined_message_handler

    class FormOfAddress:
        def __init__(self, me: str = None, other: str = None):
            self.me = me
            self.other = other

    class UndefinedMessageHandler:
        def __init__(
            self,
            type: "LocalData.UndefinedMessageHandlerType" = None,
            message: str = None,
        ):
            self.type = type
            self.message = message

    class UndefinedMessageHandlerType(Enum):
        RESPONSE = "response"
        NOTIFY = "notify"


# Đọc dữ liệu từ file JSON
def read_json_file(file_path: str) -> LocalData:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

        # Create form_of_address object from JSON data
        form_of_address = LocalData.FormOfAddress(
            me=data["FORM_OF_ADDRESS"]["ME"], other=data["FORM_OF_ADDRESS"]["OTHER"]
        )

        # Create undefined_message_handler object from JSON data
        handler_type = LocalData.UndefinedMessageHandlerType.RESPONSE
        if data["UNDEFINED_MESSAGE_HANDLER"]["TYPE"].lower() == "notify":
            handler_type = LocalData.UndefinedMessageHandlerType.NOTIFY

        undefined_message_handler = LocalData.UndefinedMessageHandler(
            type=handler_type, message=data["UNDEFINED_MESSAGE_HANDLER"]["MESSAGE"]
        )

        # Create and return LocalData object
        return LocalData(
            drive_folder_id=data["DRIVE_FOLDER_ID"],
            chat_wait_seconds=float(data["CHAT_WAIT_SECONDS"]),
            sentiment_interval_chat_count=int(data["SENTIMENT_INTERVAL_CHAT_COUNT"]),
            form_of_address=form_of_address,
            reaction_message=data["REACTION_MESSAGE"],
            undefined_message_handler=undefined_message_handler,
        )


# Sử dụng
file_path = "./app/stores/localData.json"
LOCAL_DATA = read_json_file(file_path)
