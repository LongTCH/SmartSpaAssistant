from dataclasses import dataclass
from datetime import datetime

import pytz
from app.baml_agents.utils import BAMLAgentRunResult, construct_output_langfuse
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage
from langfuse.decorators import langfuse_context, observe


@dataclass
class SyntheticAgentDeps:
    script_context: str
    sheet_context: str
    context_memory: str
    timezone: str = "Asia/Ho_Chi_Minh"


class SyntheticAgent:
    CONFIG = {
        "model_retries": 2,
    }

    @observe(as_type="generation", name="synthetic_agent")
    async def run(
        self,
        user_prompt: str,
        deps: SyntheticAgentDeps,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[str]:
        collector = baml_options.get("collector", None)
        dynamic_prompt = self.get_current_local_time(deps)
        dynamic_prompt += self.get_scripts_context(deps)
        dynamic_prompt += await self.get_sheet_context(deps)
        new_message = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        model_retries = self.CONFIG["model_retries"]
        while True:
            try:
                agent_response: str = await b.SyntheticAgent(
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
                new_message.append(
                    BAMLMessage(role="assistant", content=agent_response)
                )
                return BAMLAgentRunResult[str](
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

    def get_scripts_context(self, deps: SyntheticAgentDeps) -> str:
        script_context = deps.script_context
        if not script_context:
            return ""
        return f"\nRelevant information from scripts:\n{script_context}"

    async def get_sheet_context(self, deps: SyntheticAgentDeps) -> str:
        sheet_context = deps.sheet_context
        if not sheet_context:
            return ""
        return f"\n## Relevant information from sheet data:\n{sheet_context}\n"

    def get_current_local_time(self, deps: SyntheticAgentDeps) -> str:
        """
        Get the current local time.
        """
        tz = pytz.timezone(deps.timezone)
        local_time = datetime.now(tz)
        return f"Current local time at {deps.timezone} is: {str(local_time)}\n"


synthetic_agent = SyntheticAgent()
