from typing import Dict, Literal, Union

from app.configs import env_config
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

ModelName = Literal[
    "gpt-4o",
    "gpt-4o-mini",
    "deepseek-chat",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o4-mini",
    "o3",
    "o3-mini",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-flash-lite" "gemini-2.5-flash",
    "gemini-2.5-flash-thinking",
    "gemini-2.5-pro",
    "qwen-2.5-coder",
    "deepseek-reasoner",
    "grok-3-mini-beta",
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
    "o3": OpenAIModel(
        "o3",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "o3-mini": OpenAIModel(
        "o3-mini",
        provider=OpenAIProvider(api_key=env_config.OPENAI_API_KEY),
    ),
    "deepseek-chat": OpenAIModel(
        "deepseek-chat",
        provider=DeepSeekProvider(api_key=env_config.DEEPSEEK_API_KEY),
    ),
    "deepseek-reasoner": OpenAIModel(
        "deepseek-reasoner",
        provider=DeepSeekProvider(api_key=env_config.DEEPSEEK_API_KEY),
    ),
    "qwen-2.5-coder": OpenAIModel(
        "qwen/qwen-2.5-coder-32b-instruct:free",
        provider=OpenRouterProvider(api_key=env_config.OPENROUTER_API_KEY),
    ),
    "gemini-2.5-flash-thinking": OpenAIModel(
        "google/gemini-2.5-flash-preview-05-20:thinking",
        provider=OpenRouterProvider(api_key=env_config.OPENROUTER_API_KEY),
    ),
    "gemini-2.5-flash-lite": GeminiModel(
        "gemini-2.5-flash-lite-preview-06-17",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
    "gemini-2.0-flash-lite": GeminiModel(
        "gemini-2.0-flash-lite",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
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
        "gemini-2.5-pro-preview-06-05",
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
    "gemini-1.5-flash": GeminiModel(
        "gemini-flash-1.5",
        provider=GoogleGLAProvider(
            api_key=env_config.GEMINI_API_KEY,
        ),
    ),
}
