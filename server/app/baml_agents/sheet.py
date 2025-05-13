import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytz
from app.baml_agents.utils import (
    BAMLAgentRunResult,
    BAMLModelRetry,
    construct_output_langfuse,
    dump_json,
)
from app.configs.database import async_session, with_session
from app.repositories import sheet_repository
from app.utils.agent_utils import is_read_only_sql, normalize_postgres_query
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage, SheetAgentOutput
from fuzzywuzzy import process
from langfuse.decorators import langfuse_context, observe
from pydantic import BaseModel
from sqlalchemy import text


@dataclass
class SheetAgentDeps:
    script_context: str
    timezone: str = "Asia/Ho_Chi_Minh"


class SQLExecutionMessage(BaseModel):
    sql_query: str
    result: list[dict[str, Any]]

    def __str__(self):
        return self.model_dump_json()


class SheetAgent:

    # Constants for model and SQL retry configuration
    CONFIG = {
        "model_retries": 3,
        "sql_empty_data_retries": 2,
    }

    @observe(as_type="generation", name="sheet_agent")
    async def run(
        self,
        user_prompt: str,
        deps: SheetAgentDeps,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[SQLExecutionMessage]:
        collector = baml_options.get("collector", None)
        dynamic_prompt = self.get_current_local_time(deps)
        dynamic_prompt += self.get_scripts_context(deps)
        dynamic_prompt += await self.get_all_available_sheets()
        new_messages = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        model_retries = self.CONFIG["model_retries"]
        sql_empty_data_retries = self.CONFIG["sql_empty_data_retries"]
        while True:
            try:
                agent_response: SheetAgentOutput = await b.SheetAgent(
                    dynamic_system_prompt=dynamic_prompt,
                    user_prompt=user_prompt,
                    message_history=message_history,
                    baml_options=baml_options,
                )
                if collector:
                    last_log = collector.last
                    langfuse_context.update_current_observation(
                        usage_details={
                            "input": last_log.usage.input_tokens,
                            "output": last_log.usage.output_tokens,
                        },
                        start_time=last_log.timing.start_time_utc_ms,
                        end_time=last_log.timing.start_time_utc_ms
                        + last_log.timing.duration_ms,
                        model=last_log.calls[-1].client_name,
                        output=construct_output_langfuse(
                            collector, last_log.raw_llm_response
                        ),
                    )
                sql_query = agent_response.sql_query
                new_messages.append(
                    BAMLMessage(
                        role="assistant", content=agent_response.model_dump_json()
                    )
                )
                try:
                    rows = await self.execute_query_on_sheet_rows(sql_query)
                    # if rows is empty, raise BAMLModelRetry
                    if not rows and sql_empty_data_retries > 0:
                        sql_empty_data_retries -= 1
                        raise BAMLModelRetry(
                            "No data found. Please check your query again."
                            "If your query contain fulltext search, such as data &@~ 'example keyword', that will search rows contain both 'example' and 'keyword'."
                            "Prefer using less keywords or using OR to combine them. Please check your keywords."
                        )
                except BAMLModelRetry as model_retry:
                    raise model_retry
                except Exception as e:
                    print(f"Error executing query: {e}")
                    raise BAMLModelRetry(
                        f"Error executing query: {str(e)}. Please check your query again."
                    )
                sql_execution_message = SQLExecutionMessage(
                    sql_query=sql_query, result=rows
                )
                new_messages.append(
                    BAMLMessage(
                        role="assistant",
                        content=sql_execution_message.model_dump_json(),
                    )
                )
                return BAMLAgentRunResult[SQLExecutionMessage](
                    output=sql_execution_message,
                    new_message=new_messages,
                    message_history=message_history,
                )
            except Exception as e:
                if model_retries > 0:
                    model_retries -= 1
                    new_messages.append(BAMLMessage(role="assistant", content=str(e)))
                    continue
                else:
                    raise e

    def get_scripts_context(self, deps: SheetAgentDeps) -> str:
        script_context = deps.script_context
        if not script_context:
            return ""
        return f"\nRelevant information from scripts:\n{script_context}"

    def get_current_local_time(self, deps: SheetAgentDeps) -> str:
        """
        Get the current local time.
        """
        tz = pytz.timezone(deps.timezone)
        local_time = datetime.now(tz)
        return f"Current local time at {deps.timezone} is: {str(local_time)}\n"

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
            sheet_list = [
                {
                    "name": sheet.name,
                    "description": sheet.description,
                    "column_config": sheet.column_config,
                    "table_name": sheet.table_name,
                }
                for sheet in sheets
            ]
            return f"\nHere are relevant sheets:\n{dump_json(sheet_list)}"
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


sheet_agent = SheetAgent()
