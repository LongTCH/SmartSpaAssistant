from dataclasses import dataclass

from app.agents.model_hub import model_hub
from app.configs.database import with_session
from app.repositories import sheet_repository
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings


@dataclass
class ScriptRetrieveAgentDeps:
    user_input: str
    user_id: str
    script_context: str


class ScriptRetrieveAgentOutput(BaseModel):
    pieces_of_information: list[str]


instructions = """
You are a helpful ai extractor assistant.
You will be provided with customer's message and a list of scripts.
Rerank and filter relevant information from the scripts.
Provide more information about the customer's needs.
Think if information from scripts are enough to answer the customer's needs, OR any information instruct you to prompt more from customers to clarify their needs.
if you need to prompt more from customer, please provide a list of pieces of information that you need to ask the customer.
Notice that your response will be the instructions for the next agent, who doesn't know about scripts, so it must contains more information as possible.
Your response will contain a list of pieces of information, each piece of information should be standalone script after rerank and filter. Each piece of information should be a detailed explanation of the customer's needs.
Must not contain information that you can see in the previous chat history. Just contain new information.
Response in customer's language.
"""
model = model_hub["gpt-4o-mini"]
script_retrieve_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    output_type=ScriptRetrieveAgentOutput,
    output_retries=3,
    model_settings=ModelSettings(temperature=0),
)


# @script_retrieve_agent.output_validator
# async def validate_output(
#     context: RunContext[ScriptRetrieveAgentOutput], output: ScriptRetrieveAgentOutput
# ) -> ScriptRetrieveAgentOutput:
#     if len(output.pieces_of_information) < 3:
#         raise ModelRetry(
#             "Please return at least 3 pieces of detailed information.")
#     return output


@script_retrieve_agent.instructions
async def get_scripts_context(
    context: RunContext[ScriptRetrieveAgentDeps],
) -> str:
    """
    Get all associated scripts from the database.
    """
    script_context = context.deps.script_context
    if not script_context:
        return ""
    return f"\nRelevant information from scripts:\n{script_context}"


@script_retrieve_agent.instructions
async def get_all_available_sheets(context: RunContext[ScriptRetrieveAgentDeps]) -> str:
    """
    Get associated sheet from the database.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        if not sheets:
            return "No available sheets. So set should_query_sheet to False."
        sheets_desc = ""
        for sheet in sheets:
            sheets_desc += (
                f"Sheet name: {sheet.name}\n Sheet description: {sheet.description}\n"
                "----------------------------------\n"
                # "Sheet columns:\n"
            )
            # for column in sheet.column_config:
            #     sheets_desc += (
            #         f"Column name: {column['column_name']}\n"
            #         f"Column description: {column['description']}\n"
            #     )
        return (
            "Here is relevant sheets that help you to decide if we need query from sheets:\n"
            "Carefully study the description description of each sheet.\n"
            f"{sheets_desc}"
        )
    except Exception as e:
        return f"Error fetching sheets: {str(e)}"


@script_retrieve_agent.instructions
async def chain_of_thought(
    context: RunContext[ScriptRetrieveAgentDeps],
) -> str:
    """
    Chain of thought for the agent.
    """
    return """
    Before you answer, please explain your reasoning step-by-step.

    For example:
    If we think step by step we can see that ...
    Therefore the output is:
    {
      ... // schema
    }"""
