from app.configs.database import with_session
from app.dtos.setting_dtos import SettingDetailsDto
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
from app.services import setting_service
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.google import GoogleModelSettings, ThinkingConfigDict


async def get_instruction(context: RunContext[SyntheticAgentDeps]) -> str:
    guest_id = context.deps.user_id

    setting = await with_session(
        lambda session: setting_service.get_setting_details(session)
    )
    setting = SettingDetailsDto(**setting)
    bot_identity = setting.identity
    bot_instructions = setting.instructions
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

    await get_all_available_sheets(context)

    # Template as Python string
    rendered = f"""<customer_id>
{guest_id}
</customer_id>
<identity>
{bot_identity}
</identity>
<customer>
<customer_info>
    <name>{customer_name}</name>
    <gender>{customer_gender}</gender>
    <phone>{customer_phone}</phone>
    <email>{customer_email}</email>
    <address>{customer_address}</address>
    <birthday>{customer_birthday}</birthday>
</customer_info>
<instructions>
{bot_instructions}
- Only use retrieved context and never rely on your own knowledge for any of these questions.
- However, if you don't have enough information to properly call the tool, ask the user for the information you need.
- Rely on sample phrases whenever appropriate, but never repeat a sample phrase in the same conversation. Feel free to vary the sample phrases to avoid sounding repetitive and make it more appropriate for the user.
- You should divide your response into multiple parts using markdown separator --- for easier reading.
</instructions>"""

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
