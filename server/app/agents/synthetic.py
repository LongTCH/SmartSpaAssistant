from dataclasses import dataclass
from datetime import datetime

import pytz
from app.configs import env_config
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


@dataclass
class SyntheticAgentDeps:
    user_input: str
    user_id: str
    script_context: str
    context_memory: str
    sheet_context: str | None
    timezone: str = "Asia/Ho_Chi_Minh"


instructions = """
You are Nguyen Thi Phuong Thao, a 25‑year‑old female customer service specialist at Mailisa Spa (skin care). You are dynamic, polite, supportive, well‑explained, and soft‑spoken. Always respond promptly with real data—never say you’ll “look up information later.”
You will response in customer's language, make the answer humanized, and use emojis to make the conversation more engaging. You are not a bot, so avoid using technical terms or jargon.
BEHAVIOR:
1. Think carefully before answering. If you don’t know after careful consideration, honestly say so and suggest contacting our HOTLINE 09001011 or visiting a Mailisa Spa location.
2. Always include accurate information provided—never guess or fabricate.
3. Provide extra useful insights (related products, skincare tips, promotions) to delight and guide the customer, but keep replies concise and focused.
4. You may share media via links when helpful.
5. Strongly focus on answering right pointedly and enoughly, just provide additional information if needed.

GOAL:
Deliver accurate, engaging, and value‑added answers that showcase Mailisa’s expertise and encourage customers to book treatments or purchase products.
"""
model = OpenAIModel(
    "deepseek-chat",
    provider=OpenAIProvider(
        base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
    ),
)

synthetic_agent = Agent(
    model="openai:gpt-4o-mini",
    instructions=instructions,
    retries=2,
    output_type=str,
    output_retries=3,
    model_settings=ModelSettings(temperature=0, timeout=120),
)


# @sheet_agent.output_validator
# async def validate_sheet_output(
#     context: RunContext[None], output: str
# ) -> str:
#     """
#     Validate the output of the sheet agent.
#     """
#     if not isinstance(output, str):
#         raise ModelRetry("Invalid output format. Expected a string.")
#     response: AgentRunResult = await check_wait_resp_agent.run(user_prompt=output)
#     if "True" in response.output:
#         raise ModelRetry(
#             "Response indicates that the user should wait. Please retry to avoid making the user wait."
#         )
#     return output


@synthetic_agent.instructions
async def get_current_local_time(context: RunContext[SyntheticAgentDeps]) -> str:
    """
    Get the current local time.
    """
    tz = pytz.timezone(context.deps.timezone)
    local_time = datetime.now(tz)
    return f"Current local time at {context.deps.timezone} is: {str(local_time)}\n"


@synthetic_agent.instructions
async def get_sheet_context(
    context: RunContext[SyntheticAgentDeps],
) -> str:
    sheet_context = context.deps.sheet_context
    if not sheet_context:
        return ""
    return f"\n## Relevant information from sheet data:\n{sheet_context}\n"


@synthetic_agent.instructions
async def get_context_memory(context: RunContext[SyntheticAgentDeps]) -> str:
    """
    Get context memory from the database.
    """
    context = context.deps.context_memory
    if not context:
        return ""
    return f"\n## Relevant information from previous conversations:\n{context}"


@synthetic_agent.instructions
async def get_all_associated_scripts(
    context: RunContext[SyntheticAgentDeps],
) -> str:
    """
    Get all associated scripts from the database.
    """
    script_context = context.deps.script_context
    if not script_context:
        return ""
    return f"\n## Relevant information from scripts:\n{script_context}\n"
