from app.agents.model_hub import model_hub
from app.utils.agent_utils import MessagePart
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings


class SyntheticAgentOutput(BaseModel):
    message_parts: list[MessagePart] = Field(
        description=(
            "List of message parts returned by the agent after breaking long single message into multiple parts "
        )
    )


instructions = """
You are a helpful AI assistant.
Your job is to break response into multiple messages if the response is long, but group relevant messages to make consistent.
Each message must be less than 50 words.
Please do not change the content of the response.
Response in customer's language.
"""
model = model_hub["gpt-4o-mini"]
message_split_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    output_type=SyntheticAgentOutput,
    output_retries=3,
    model_settings=ModelSettings(temperature=0),
)
