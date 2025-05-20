from dataclasses import dataclass

from app.pydantic_agents.model_hub import model_hub
from pydantic_ai import Agent, RunContext


@dataclass
class MemoryAgentDeps:
    summaries: list[str]


# And importantly, you will be given latest messages of the customer and the assistant.
# You can refer to the chat history for better understanding.

instructions = """
You are a helpful ai extractor assistant.
You will be given an interval of chat history summaries between the customer and the assistant.
Your task is to extract the most new important keywords to describe customer's insight and information, mainly using latest messages, into a string.
NOTICE: Just extract the new keywords, do not repeat the old keywords.
This string will be stored in database as long-term memory, so keep it short, concise and relevant.
Please write in customer's language.
"""

model = model_hub["gemini-1.5-flash-8b"]
memory_agent = Agent(model=model, instructions=instructions, retries=2)


@memory_agent.instructions
async def get_summaries(
    context: RunContext[MemoryAgentDeps],
) -> str:
    """
    Get summaries from the context.
    """
    return "Below are some summaries of the conversation:\n" + "\n".join(
        context.deps.summaries
    )
