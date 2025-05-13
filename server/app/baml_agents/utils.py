from typing import Any, Generic, TypeVar

import pydantic
from baml_client.types import BAMLMessage
from baml_py import Collector
from pydantic import BaseModel, TypeAdapter

T = TypeVar("T")
BAMLMessagesTypeAdapter = pydantic.TypeAdapter(
    list[BAMLMessage],
    config=pydantic.ConfigDict(
        defer_build=True, ser_json_bytes="base64", val_json_bytes="base64"
    ),
)


class BAMLAgentRunResult(BaseModel, Generic[T]):
    output: T
    message_history: list[BAMLMessage] = []
    new_messages: list[BAMLMessage] = []

    def new_messages_json(self) -> bytes:
        return BAMLMessagesTypeAdapter.dump_json(self.new_messages)

    def all_messages_json(self) -> bytes:
        return BAMLMessagesTypeAdapter.dump_json(
            [*self.message_history, *self.new_messages]
        )


class BAMLModelRetry(Exception):
    pass


def dump_json(data: Any, *, indent: int = None, exclude_none: bool = False) -> str:
    """
    Tuần tự hóa dữ liệu thành chuỗi JSON, hỗ trợ các kiểu dữ liệu phức tạp.

    :param data: Dữ liệu cần tuần tự hóa (có thể là mô hình Pydantic, danh sách, từ điển, v.v.).
    :param indent: Số khoảng trắng để thụt lề trong chuỗi JSON (mặc định là None).
    :param exclude_none: Loại bỏ các trường có giá trị None nếu đặt là True.
    :return: Chuỗi JSON đại diện cho dữ liệu.
    """
    adapter = TypeAdapter(type(data))
    return adapter.dump_json(data, indent=indent, exclude_none=exclude_none).decode(
        "utf-8"
    )


def construct_output_langfuse(collector: Collector, output: Any) -> dict[str, Any]:
    """
    Trả về dict prompt từ body.
    """
    last_log = collector.last
    last_call = last_log.calls[-1]
    body = last_call.http_request.body.json()
    return {"final_output": output, "body": body}
