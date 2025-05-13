from typing import Dict, Literal, Union

from app.configs import env_config
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

ModelName = Literal["gpt-4o-mini", "deepseek-chat", "gemini-2.0-flash-lite"]
ModelType = Union[OpenAIModel, GeminiModel]


model_hub: Dict[ModelName, ModelType] = {
    "gpt-4o-mini": OpenAIModel(
        "gpt-4o-mini",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "gpt-4.1-nano": OpenAIModel(
        "gpt-4.1-nano",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "deepseek_chat": OpenAIModel(
        "deepseek-chat",
        provider=OpenAIProvider(
            base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
        ),
    ),
    "gemini-2.0-flash-lite": GeminiModel(
        "gemini-2.0-flash-lite",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
}
