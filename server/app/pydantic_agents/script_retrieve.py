from dataclasses import dataclass

from app.pydantic_agents.model_hub import model_hub
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings


@dataclass
class ScriptRetrieveAgentDeps:
    script_context: str


instructions = """
You are a helpful ai rerank assistant.
You will be given a list of origin scripts in XML format.
You need to return all most relevant scripts solution in list of string.
If you cannot find any relevant scripts, return an empty list.
"""
model = model_hub["gemini-2.0-flash-lite"]
script_retrieve_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    output_type=list[str],
    model_settings=ModelSettings(temperature=0),
)


@script_retrieve_agent.instructions
async def get_scripts_context(
    context: RunContext[ScriptRetrieveAgentDeps],
) -> str:
    """
    Get all associated scripts from the database.
    """
    return f"\nRelated scripts in XML format:\n{context.deps.script_context}"
