import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytz
from app.baml_agents.utils import (
    BAMLAgentRunResult,
    BAMLModelRetry,
    dump_json,
    update_log,
)
from app.configs.database import async_session, with_session
from app.repositories import sheet_repository
from app.utils.agent_utils import is_read_only_sql, normalize_postgres_query
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import (
    BAMLMessage,
    ChatResponseItem,
    GetAllSheetsTool,
    OutputTool,
    SQLQueryTool,
)
from fuzzywuzzy import process
from langfuse.decorators import observe
from pydantic import BaseModel
from sqlalchemy import text


@dataclass
class MasterAgentDeps:
    script_context: str
    context_memory: str
    timezone: str = "Asia/Ho_Chi_Minh"


class FunctionDetails(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str = "call_" + str(uuid.uuid4())
    type: str = "function"
    function: FunctionDetails


class ToolCallOutput(BaseModel):
    id: str
    name: str
    content: Any


class ToolCallsWrapper(BaseModel):
    tool_calls: list[ToolCall]


class MasterAgent:
    CONFIG = {
        "model_retries": 0,
        "max_calls": 5,
    }

    @observe(as_type="generation", name="master_agent")
    async def run(
        self,
        user_prompt: str,
        deps: MasterAgentDeps,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[list[ChatResponseItem]]:
        collector = baml_options.get("collector", None)
        dynamic_prompt = self.get_current_local_time(deps)
        # dynamic_prompt += await self.get_all_available_sheets()
        dynamic_prompt += self.get_scripts_context(deps)
        new_messages = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        model_retries = self.CONFIG["model_retries"]
        for i in range(self.CONFIG["max_calls"]):
            try:
                tools = await b.MasterAgent(
                    dynamic_system_prompt=dynamic_prompt,
                    user_prompt=user_prompt,
                    message_history=message_history + new_messages,
                    baml_options=baml_options,
                )
                update_log(collector)
                tool_messages = []
                tool_calls: list[ToolCall] = []
                for tool in tools:
                    if isinstance(tool, GetAllSheetsTool):
                        function_details = FunctionDetails(
                            name=tool.tool_name, arguments=""
                        )
                        tool_call = ToolCall(function=function_details)
                        tool_calls.append(tool_call)
                        result = await self.get_all_available_sheets()
                        tool_call_output = ToolCallOutput(
                            id=tool_call.id, name=tool.tool_name, content=result
                        )
                        tool_messages.append(
                            BAMLMessage(
                                role="assistant",
                                content=tool_call_output.model_dump_json(),
                            )
                        )
                        update_log(collector)

                    elif isinstance(tool, SQLQueryTool):
                        # If the tool is a SQLQueryTool, execute the query
                        function_details = FunctionDetails(
                            name=tool.tool_name, arguments=tool.query
                        )
                        tool_call = ToolCall(function=function_details)
                        tool_calls.append(tool_call)
                        sql_query = tool.query
                        result = await self.execute_query_on_sheet_rows(sql_query)
                        tool_call_output = ToolCallOutput(
                            id=tool_call.id, name=tool.tool_name, content=result
                        )
                        tool_messages.append(
                            BAMLMessage(
                                role="assistant",
                                content=tool_call_output.model_dump_json(),
                            )
                        )
                        update_log(collector)
                    elif isinstance(tool, OutputTool):
                        # If the tool is an OutputTool, return the output
                        new_messages.append(
                            BAMLMessage(
                                role="assistant", content=dump_json(tool.message_parts)
                            )
                        )
                        update_log(collector)
                        return BAMLAgentRunResult[list[ChatResponseItem]](
                            output=tool.message_parts,
                            new_messages=new_messages,
                            message_history=message_history,
                        )
                if tool_calls:
                    tool_calls_wrapper = ToolCallsWrapper(tool_calls=tool_calls)
                    new_messages.append(
                        BAMLMessage(
                            role="assistant", content=dump_json(tool_calls_wrapper)
                        )
                    )
                    new_messages.extend(tool_messages)
            except Exception as e:
                if model_retries > 0:
                    model_retries -= 1
                    continue
                else:
                    raise e

    def get_scripts_context(self, deps: MasterAgentDeps) -> str:
        script_context = deps.script_context
        if not script_context:
            return ""
        return f"\nStrictly follow these instructions:\n{script_context}"

    # async def get_sheet_context(self, deps: MasterAgentDeps) -> str:
    #     sheet_context = deps.sheet_context
    #     if not sheet_context:
    #         return ""
    #     return f"\n## Relevant information from sheet data, should use to response:\n{sheet_context}\n"

    def get_current_local_time(self, deps: MasterAgentDeps) -> str:
        """
        Get the current local time.
        """
        tz = pytz.timezone(deps.timezone)
        local_time = datetime.now(tz)
        return f"\nCurrent local time at {deps.timezone} is: {str(local_time)}\n"

    async def get_all_available_sheets(self) -> str:
        """
        Get associated sheet from the database.
        """
        try:
            sheets = await with_session(
                lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
            )
            if not sheets:
                return "No available sheets"
            sheets_desc = ""
            for sheet in sheets:
                sheets_desc += (
                    f'Sheet ID: "{sheet.id}"\n Sheet name: {sheet.name}\n Sheet description: {sheet.description}\n Table name: {sheet.table_name}\n'
                    "Sheet columns:\n"
                )
                for column in sheet.column_config:
                    sheets_desc += (
                        f"Column name: {column['column_name']}\n"
                        f"Column description: {column['description']}\n"
                        f"Column type: {column['column_type']}\n"
                        f"Column is index: {column['is_index']}\n"
                        "--------------------\n"
                    )
            return (
                "\nHere are relevant sheets:\n"
                "Carefully study the description and columns description of each sheet.\n"
                f"{sheets_desc}"
            )
        except Exception as e:
            return f"Error fetching sheets: {str(e)}"

    @observe(as_type="generation", name="execute_query_on_sheet_rows")
    async def execute_query_on_sheet_rows(self, query: str) -> list[dict[str, Any]]:
        async with async_session() as db:
            query = normalize_postgres_query(query)
            if not is_read_only_sql(query):
                raise BAMLModelRetry(
                    "Query must be read-only SQL. Please check your query again."
                )
            sheets = await sheet_repository.get_all_sheets_by_status(db, "published")
            table_names = [sheet.table_name for sheet in sheets]
            query = self.replace_table_if_needed(query, table_names)
            # execute the query and return the result
            result = await db.execute(text(query))
            # Fetch all results as Dictionaries
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    def get_table_name_from_query(self, query: str) -> str:
        """
        Extract table name after FROM clause, handling both single and double quotes.
        """
        # Try to find table name in double quotes first
        match = re.search(r'FROM\s+"([^"]+)"', query, re.IGNORECASE)
        if match:
            return match.group(1)

        # If not found, try with single quotes
        match = re.search(r"FROM\s+'([^']+)'", query, re.IGNORECASE)
        if match:
            return match.group(1)

        # If still not found, try without quotes
        match = re.search(r"FROM\s+([a-zA-Z0-9_]+)", query, re.IGNORECASE)
        if match:
            return match.group(1)

        raise BAMLModelRetry("Could not find table name in query.")

    def replace_table_if_needed(
        self, query: str, available_table_names: list[str], min_score: int = 60
    ) -> str:
        # Extract table name from query
        try:
            table_in_query = self.get_table_name_from_query(query)
        except BAMLModelRetry:
            # If we can't extract the table name, return the query unchanged
            return query

        # If table name is not in the list, find and replace
        if table_in_query not in available_table_names:
            best_table, score_table = process.extractOne(
                table_in_query, available_table_names
            )
            if score_table < min_score:
                raise BAMLModelRetry(
                    f"Invalid table name: {table_in_query}. "
                    f"Best match '{best_table}' has only {score_table} points."
                )

            # Replace table name in FROM clause with the best match
            query = query.replace(table_in_query, best_table)

        return query


master_agent = MasterAgent()
