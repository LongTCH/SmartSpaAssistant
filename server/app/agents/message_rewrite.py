from app.configs import env_config
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

instructions = """
You are a helpful ai extractor assistant.
From customer's message, you will rewrite customer's needs as a string query in customer's language.
Fix the grammar and spelling errors.
Response in customer's language.
"""
model = OpenAIModel(
    "deepseek-chat",
    provider=OpenAIProvider(
        base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
    ),
)
message_rewrite_agent = Agent(
    model="openai:gpt-4.1-nano",
    instructions=instructions,
    retries=2,
    model_settings=ModelSettings(temperature=0, timeout=120),
)
