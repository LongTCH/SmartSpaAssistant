from dataclasses import dataclass

from app.configs import env_config
from app.configs.database import with_session
from app.repositories import sheet_repository
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


@dataclass
class ScriptRetrieveAgentDeps:
    user_input: str
    user_id: str
    script_context: str


class ScriptRetrieveAgentOutput(BaseModel):
    should_query_sheet: bool
    pieces_of_information: list[str]


instructions = """
You are a helpful ai extractor assistant.
You will be provided with customer's message and a list of scripts.
Carefully study the scripts to define if we should query more from sheets.
Provide more information about the customer's needs.
Notice that your response will be the context for the next agent, who doesn't know about scripts, so it must contains more information as possible.
Your response will contain the following:
- A boolean value indicating if we should query more from sheets.
- A list of pieces of information, each piece of information should be standalone and not depend on the answer of any other piece of information. Each piece of information should be a detailed explanation of the customer's needs. Return at least 5 pieces of detailed information.
NOTE:
- If you set should_query_sheet to False, it means that you you decided information from scripts are enough to answer the customer's needs, and you need to provide detailed pieces of information that used to answer the customer's needs.
- If you set should_query_sheet to True, it means that you need to query more from sheets, and you need to provide detailed pieces of information that can instruct other agents to fulfill the customer's needs.
Response in customer's language.
"""
model = OpenAIModel(
    "deepseek-chat",
    provider=OpenAIProvider(
        base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
    ),
)
script_retrieve_agent = Agent(
    model="openai:gpt-4o-mini",
    instructions=instructions,
    retries=2,
    output_type=ScriptRetrieveAgentOutput,
    output_retries=3,
    model_settings=ModelSettings(temperature=0, timeout=120),
)


@script_retrieve_agent.output_validator
async def validate_output(
    context: RunContext[ScriptRetrieveAgentOutput], output: ScriptRetrieveAgentOutput
) -> ScriptRetrieveAgentOutput:
    if len(output.pieces_of_information) < 5:
        raise ModelRetry("Please return at least 5 pieces of detailed information.")
    return output


@script_retrieve_agent.instructions
async def get_scripts_context(
    context: RunContext[ScriptRetrieveAgentDeps],
) -> str:
    """
    Get all associated scripts from the database.
    """
    script_context = context.deps.script_context
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
        sheets_desc = ""
        for sheet in sheets:
            sheets_desc += (
                f"Sheet name: {sheet.name}\n Sheet description: {sheet.description}\n"
                "Sheet columns:\n"
            )
            for column in sheet.column_config:
                sheets_desc += (
                    f"Column name: {column['column_name']}\n"
                    f"Column description: {column['description']}\n"
                )
        # for i, sheet in enumerate(sheets):
        #     example = await with_session(
        #         lambda session: sheet_repository.get_example_rows_by_sheet_id(
        #             session, sheet.id)
        #     )
        #     sheet_list[i]["example_rows"] = limit_sample_rows_content(example)
        return (
            "\nHere is relevant sheets that help you to decide if we need query from sheets:\n"
            "Carefully study the description and columns description of each sheet.\n"
            f"{sheets_desc}"
        )
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"
