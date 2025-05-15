from app.baml_agents.utils import BAMLAgentRunResult, construct_output_langfuse
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage
from langfuse.decorators import langfuse_context, observe


class MemoryAgent:
    CONFIG = {
        "model_retries": 0,
    }

    @observe(as_type="generation", name="memory_agent")
    async def run(
        self,
        user_prompt: str,
        deps: None = None,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[str]:
        collector = baml_options.get("collector", None)
        new_message = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        while True:
            try:
                agent_response: str = await b.MemoryAgent(
                    user_prompt, baml_options=baml_options
                )
                new_message.append(
                    BAMLMessage(role="assistant", content=agent_response)
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
                return BAMLAgentRunResult(
                    output=agent_response,
                    new_message=new_message,
                    message_history=message_history,
                )
            except Exception as e:
                if self.CONFIG["model_retries"] > 0:
                    self.CONFIG["model_retries"] -= 1
                    continue
                else:
                    raise e


memory_agent = MemoryAgent()
