from app.baml_agents.utils import BAMLAgentRunResult, dump_json, update_log
from baml_client.async_client import BamlCallOptions, b
from baml_client.types import BAMLMessage, ChatResponseItem
from langfuse.decorators import observe


class MessageSplitAgent:
    CONFIG = {
        "model_retries": 0,
    }

    @observe(as_type="generation", name="message_split_agent")
    async def run(
        self,
        user_prompt: str,
        deps: None = None,
        message_history: list[BAMLMessage] = [],
        baml_options: BamlCallOptions = {},
    ) -> BAMLAgentRunResult[list[ChatResponseItem]]:
        collector = baml_options.get("collector", None)
        model_retries = self.CONFIG["model_retries"]
        new_messages = [
            BAMLMessage(role="user", content=user_prompt),
        ]
        while True:
            try:
                agent_response: list[ChatResponseItem] = await b.MessageSplitAgent(
                    user_prompt, baml_options=baml_options
                )
                update_log(collector)
                new_messages.append(
                    BAMLMessage(role="assistant", content=dump_json(agent_response))
                )
                return BAMLAgentRunResult[list[ChatResponseItem]](
                    output=agent_response,
                    new_messages=new_messages,
                    message_history=message_history,
                )
            except Exception as e:
                if model_retries > 0:
                    model_retries -= 1
                    continue
                else:
                    raise e


message_split_agent = MessageSplitAgent()
