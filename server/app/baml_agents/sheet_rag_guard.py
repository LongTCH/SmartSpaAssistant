from dataclasses import dataclass
from datetime import datetime

import pytz
from app.baml_agents.utils import (
    BAMLAgentRunResult,
    BAMLModelRetry,
    construct_output_langfuse,
    dump_json,
)
from app.configs.database import with_session
from app.repositories import sheet_repository
from app.services.integrations import sheet_rag_service
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage
from fuzzywuzzy import process
from langfuse.decorators import langfuse_context, observe


@dataclass
class SheetRAGGuardAgentDeps:
    script_context: str
    rag_items: list[str]
    timezone: str = "Asia/Ho_Chi_Minh"


class SheetRAGGuardAgent:

    CONFIG = {
        "model_retries": 0,
    }

    @observe(as_type="generation", name="sheet_rag_guard_agent")
    async def run(
        self,
        user_prompt: str,
        deps: SheetRAGGuardAgentDeps,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[str]:
        collector = baml_options.get("collector", None)
        dynamic_prompt = self.get_scripts_context(deps)
        dynamic_prompt += (
            "\nBecause can not find the appropriate data matching with customer's message by SQL query.\n"
            "We retrieved relevant information items. Please carefully review the items and response with actual useful ones or ignore all and say I don't know:\n\n"
        )
        for i, item in enumerate(deps.rag_items):
            dynamic_prompt += f"Item {i + 1}:\n{item}\n\n"
        new_messages = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        model_retries = self.CONFIG["model_retries"]
        while True:
            try:
                agent_response: str = await b.SheetRAGGuardAgent(
                    dynamic_system_prompt=dynamic_prompt,
                    user_prompt=user_prompt,
                    message_history=message_history + new_messages,
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
                new_messages.append(
                    BAMLMessage(role="assistant", content=agent_response)
                )

                return BAMLAgentRunResult[str](
                    output=agent_response,
                    new_messages=new_messages,
                    message_history=message_history,
                )
            except Exception as e:
                if model_retries > 0:
                    model_retries -= 1
                    new_messages.append(BAMLMessage(role="assistant", content=str(e)))
                    continue
                else:
                    raise e

    async def rag_hybrid_search(
        self, sheet_id: str, query: str, limit: int
    ) -> list[str]:
        # replace _ to - in sheet_id
        sheet_id = sheet_id.replace("_", "-")
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        sheet_ids = [sheet.id for sheet in sheets]
        if sheet_id not in sheet_ids:
            best_id, score = process.extractOne(sheet_id, sheet_ids)
            if score < 60:
                raise BAMLModelRetry(
                    f"Invalid sheet_id: {sheet_id}. "
                    f"Best match '{best_id}' has only {score} points."
                )
            sheet_id = best_id

        sheet_chunks = await sheet_rag_service.search_chunks_by_sheet_id(
            sheet_id=sheet_id,
            query=query,
            limit=limit,
        )
        return [sheet_chunk.chunk for sheet_chunk in sheet_chunks]

    def get_scripts_context(self, deps: SheetRAGGuardAgentDeps) -> str:
        script_context = deps.script_context
        if not script_context:
            return ""
        return f"\nRelevant information from scripts:\n{script_context}"

    def get_current_local_time(self, deps: SheetRAGGuardAgentDeps) -> str:
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


sheet_rag_guard_agent = SheetRAGGuardAgent()
