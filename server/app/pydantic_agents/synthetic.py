import os

from app.configs.database import with_session
from app.pydantic_agents.model_hub import model_hub
from app.pydantic_agents.synthetic_tools import (
    SyntheticAgentDeps,
    execute_query_on_sheet_rows,
    get_all_available_sheets,
    get_current_local_time,
    get_notify_tools,
    rag_hybrid_search,
)
from app.repositories import guest_info_repository
from app.stores.store import get_local_data
from jinja2 import Environment, FileSystemLoader
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.google import GoogleModelSettings, ThinkingConfigDict


async def get_instruction(context: RunContext[SyntheticAgentDeps]) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Tạo Jinja environment từ thư mục đó
    env = Environment(loader=FileSystemLoader(current_dir))
    guest_id = context.deps.user_id

    local_data = get_local_data()
    bot_identity = local_data.identity
    bot_instructions = local_data.instructions
    guest_info = await with_session(
        lambda session: guest_info_repository.get_guest_info_by_guest_id(
            session, guest_id
        )
    )
    if not guest_info:
        customer_name = ""
        customer_gender = ""
        customer_phone = ""
        customer_email = ""
        customer_address = ""
        customer_birthday = ""
    else:
        customer_name = guest_info.fullname or ""
        customer_gender = guest_info.gender or ""
        customer_phone = guest_info.phone or ""
        customer_email = guest_info.email or ""
        customer_address = guest_info.address or ""
        customer_birthday = (
            guest_info.birthday.strftime("%Y-%m-%d") if guest_info.birthday else ""
        )
    # Load template
    template = env.get_template("synthetic_prompt.j2")
    rendered = template.render(
        customer_id=guest_id,
        bot_identity=bot_identity,
        bot_instructions=bot_instructions,
        sheets_context=await get_all_available_sheets(context),
        customer_name=customer_name,
        customer_gender=customer_gender,
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_address=customer_address,
        customer_birthday=customer_birthday,
    )
    return rendered


async def create_synthetic_agent(
    guest_id: str,
) -> Agent[SyntheticAgentDeps, str]:

    notify_tools = await get_notify_tools(guest_id)

    model = model_hub["gemini-2.5-flash"]
    synthetic_agent = Agent(
        model=model,
        instructions=get_instruction,
        retries=2,
        output_type=str,
        output_retries=2,
        model_settings=GoogleModelSettings(
            google_thinking_config=ThinkingConfigDict(
                include_thoughts=True, thinking_budget=8000
            ),
            temperature=0.0,
            # max_tokens=50000
        ),
        # model_settings=OpenAIModelSettings(
        #     # openai_reasoning_effort="high",
        #     temperature=0.1,
        # ),
        tools=[
            Tool(
                get_current_local_time,
                takes_ctx=True,
            ),
            Tool(
                get_all_available_sheets,
                takes_ctx=True,
            ),
            Tool(
                execute_query_on_sheet_rows,
                takes_ctx=False,
                max_retries=3,
                require_parameter_descriptions=True,
            ),
            Tool(
                rag_hybrid_search, takes_ctx=False, require_parameter_descriptions=True
            ),
        ]
        + notify_tools,
    )

    return synthetic_agent
