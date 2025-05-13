from dataclasses import dataclass

from app.agents.model_hub import model_hub
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings


@dataclass
class MemoryAgentDeps:
    pass


instructions = """
You are a helpful ai extractor assistant.
You will be given an interval of chat history between the customer and the assistant.
And importantly, you will be given latest messages of the customer and the assistant.
Your task is to extract the most important keywords to describe customer's insight and information, mainly using latest messages, into a string.
You can refer to the chat history for better understanding.
Please write in customer's language.
This string will be stored in database as long-term memory, so keep it short, concise and relevant.
"""

model = model_hub["gemini-2.0-flash-lite"]
memory_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    model_settings=ModelSettings(temperature=0, timeout=120),
)
