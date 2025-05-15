from dataclasses import dataclass

from app.baml_agents.utils import BAMLAgentRunResult, construct_output_langfuse
from app.configs.database import with_session
from app.repositories import sheet_repository
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage
from langfuse.decorators import langfuse_context, observe


@dataclass
class SheetGuardAgentDeps:
    script_context: str


class SheetGuardAgent:
    CONFIG = {
        "model_retries": 0,
    }

    @observe(as_type="generation", name="sheet_guard_agent")
    async def run(
        self,
        user_prompt: str,
        deps: SheetGuardAgentDeps,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[bool]:
        collector = baml_options.get("collector", None)
        model_retries = self.CONFIG["model_retries"]
        new_message = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        dynamic_prompt = self.get_scripts_context(deps)
        dynamic_prompt += await self.get_all_available_sheets()
        while True:
            try:
                agent_response: str = await b.SheetGuardAgent(
                    dynamic_prompt,
                    user_prompt,
                    message_history=[],
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
                new_message.append(
                    BAMLMessage(
                        role="assistant",
                        content=(
                            "Should query from sheets"
                            if agent_response
                            else "Should not query from sheets"
                        ),
                    )
                )
                return BAMLAgentRunResult[bool](
                    output=agent_response,
                    new_message=new_message,
                    message_history=message_history,
                )
            except Exception as e:
                if model_retries > 0:
                    model_retries -= 1
                    continue
                else:
                    raise e

    def get_scripts_context(self, deps: SheetGuardAgentDeps) -> str:
        script_context = deps.script_context
        if not script_context:
            return ""
        return f"\nRelevant information from scripts:\n{script_context}"

    async def get_all_available_sheets(self) -> str:
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
                    # "Sheet columns:\n"
                )
                # for column in sheet.column_config:
                #     sheets_desc += (
                #         f"Column name: {column['column_name']}\n"
                #         f"Column description: {column['description']}\n"
                #     )
            return (
                "\nHere is relevant sheets that help you to decide if we need query from sheets:\n"
                # "Carefully study the description and columns description of each sheet.\n"
                "Carefully study the description of each sheet.\n"
                f"{sheets_desc}"
            )
        except Exception as e:
            return f"Error fetching sheets: {str(e)}"


sheet_guard_agent = SheetGuardAgent()
