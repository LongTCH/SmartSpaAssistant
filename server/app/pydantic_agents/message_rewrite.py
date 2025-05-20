from dataclasses import dataclass

from app.pydantic_agents.model_hub import model_hub
from pydantic_ai import Agent, RunContext


@dataclass
class MessageRewriteAgentDeps:
    summaries: list[str]


instructions = """
You are a helpful ai extractor assistant.
From customer's message, you will rewrite customer's needs as a string query in customer's language.
Fix the grammar and spelling errors.
You will be provide with some summary of the conversation just use it as context.
Just rewrite the message, do not add any additional information.
Response in customer's language.
"""
model = model_hub["gemini-1.5-flash-8b"]
message_rewrite_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
)


@message_rewrite_agent.instructions
async def get_summaries(
    context: RunContext[MessageRewriteAgentDeps],
) -> str:
    """
    Get summaries from the context.
    """
    return "Below are some summaries of the conversation:\n" + "\n".join(
        context.deps.summaries
    )
