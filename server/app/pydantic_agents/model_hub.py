from typing import Dict, Literal, Union

from app.configs import env_config
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

ModelName = Literal[
    "gpt-4o-mini",
    "deepseek-chat",
    "gemini-2.0-flash-lite",
    "gpt-4.1-mini",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "qwen-2.5-coder",
    "o4-mini",
    "gpt-4.1",
    "gemini-1.5-flash-8b",
    "gpt-4o",
]
ModelType = Union[OpenAIModel, GeminiModel]


model_hub: Dict[ModelName, ModelType] = {
    "gpt-4o": OpenAIModel(
        "gpt-4o",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "gpt-4o-mini": OpenAIModel(
        "gpt-4o-mini",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "gpt-4.1-nano": OpenAIModel(
        "gpt-4.1-nano",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "deepseek-chat": OpenAIModel(
        "deepseek-chat",
        provider=OpenAIProvider(
            base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
        ),
    ),
    "qwen-2.5-coder": OpenAIModel(
        "qwen/qwen-2.5-coder-32b-instruct:free",
        provider=OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=env_config.OPENROUTER_API_KEY,
        ),
    ),
    "gemini-2.0-flash-lite": GeminiModel(
        "gemini-2.0-flash-lite",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gpt-4.1": OpenAIModel(
        "gpt-4.1",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "gpt-4.1-mini": OpenAIModel(
        "gpt-4.1-mini",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "o4-mini": OpenAIModel(
        "o4-mini",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "gemini-2.0-flash": GeminiModel(
        "gemini-2.0-flash",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gemini-1.5-pro": GeminiModel(
        "gemini-1.5-pro",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gemini-2.5-flash": GeminiModel(
        "gemini-2.5-flash-preview-05-20",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gemini-2.5-pro": GeminiModel(
        "gemini-2.5-pro-preview-05-06",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gemini-1.5-flash-8b": GeminiModel(
        "gemini-1.5-flash-8b",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
}
