from app.models import Script
from app.services.integrations import script_rag_service
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry


class ScriptRetrieveAgentOutput(BaseModel):
    pieces_of_information: list[str]


instructions = """
You are a helpful ai extractor assistant.
From customer's message, you will describe current situation and needs of the customer as a string query in user's language.
Use 'retrieve_scripts' tool which based on RAG to retrieve the most relevant scripts.
Carefully study the context of scripts to provide more information about the customer's needs.
Notice that your response will be the context for the next agent, who don't know about your scripts, so it must contains more information as possible.
You will return a list of pieces of information, each piece of information should be standalone and not depend on the answer of any other piece of information.
Return at least 5 pieces of detailed information.
"""

script_retrieve_agent = Agent(
    model="openai:gpt-4o-mini",
    instructions=instructions,
    retries=2,
    output_type=ScriptRetrieveAgentOutput,
    output_retries=3,
)


@script_retrieve_agent.output_validator
async def validate_output(
    context: RunContext[ScriptRetrieveAgentOutput], output: ScriptRetrieveAgentOutput
) -> ScriptRetrieveAgentOutput:
    if len(output.pieces_of_information) < 5:
        raise ModelRetry("Please return at least 5 pieces of detailed information.")
    return output


@script_retrieve_agent.tool_plain(retries=1)
async def retrieve_scripts(query: str) -> list[Script]:
    """
    Given a query, retrieve the most relevant scripts from the vector database.
    """
    return await script_rag_service.search_script_chunks(query, limit=5)
