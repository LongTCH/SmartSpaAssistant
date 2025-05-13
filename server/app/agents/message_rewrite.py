from app.agents.model_hub import model_hub
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

instructions = """
You are a helpful ai extractor assistant.
From customer's message, you will rewrite customer's needs as a string query in customer's language.
Fix the grammar and spelling errors.
Just rewrite the message, do not add any additional information.
Response in customer's language.
"""
model = model_hub["gemini-2.0-flash-lite"]
message_rewrite_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    model_settings=ModelSettings(temperature=0, timeout=120),
)
