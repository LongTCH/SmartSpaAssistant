from typing import Union

import pydantic
from agents.items import TResponseInputItem, TResponseOutputItem

OpenAIModelMessage = Union[TResponseOutputItem, TResponseInputItem]

OpenAIMessagesTypeAdapter = pydantic.TypeAdapter(
    list[OpenAIModelMessage],
    config=pydantic.ConfigDict(
        defer_build=True, ser_json_bytes="base64", val_json_bytes="base64"
    ),
)
