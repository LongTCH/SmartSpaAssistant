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
    update_guest_address,
    update_guest_birthday,
    update_guest_email,
    update_guest_fullname,
    update_guest_gender,
    update_guest_phone,
)
from app.repositories import guest_info_repository
from app.utils.agent_utils import MessagePart
from jinja2 import Environment, FileSystemLoader
from pydantic_ai import Agent, RunContext, Tool


async def get_instruction(context: RunContext[SyntheticAgentDeps]) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Tạo Jinja environment từ thư mục đó
    env = Environment(loader=FileSystemLoader(current_dir))
    guest_id = context.deps.user_id
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
        customer_name = guest_info.fullname
        customer_gender = guest_info.gender
        customer_phone = guest_info.phone
        customer_email = guest_info.email
        customer_address = guest_info.address
        customer_birthday = (
            guest_info.birthday.strftime("%Y-%m-%d") if guest_info.birthday else ""
        )
    # Load template
    template = env.get_template("synthetic_prompt.j2")
    rendered = template.render(
        customer_name=customer_name,
        customer_gender=customer_gender,
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_address=customer_address,
        customer_birthday=customer_birthday,
        memory_context=context.deps.context_memory,
        scripts_context=context.deps.script_context,
        sheets_context=await get_all_available_sheets(),
    )
    return rendered


async def create_synthetic_agent(
    guest_id: str,
) -> Agent[SyntheticAgentDeps, list[MessagePart]]:

    notify_tools = await get_notify_tools(guest_id)

    model = model_hub["gemini-2.5-flash"]
    synthetic_agent = Agent(
        model=model,
        instructions=get_instruction,
        retries=2,
        output_type=list[MessagePart],
        output_retries=2,
        tools=[
            Tool(
                get_all_available_sheets,
                takes_ctx=False,
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
            Tool(
                get_current_local_time,
                takes_ctx=True,
            ),
            Tool(
                update_guest_address,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
            Tool(
                update_guest_birthday,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
            Tool(
                update_guest_email,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
            Tool(
                update_guest_fullname,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
            Tool(
                update_guest_phone,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
            Tool(
                update_guest_gender,
                takes_ctx=True,
                require_parameter_descriptions=True,
            ),
        ]
        + notify_tools,
    )

    return synthetic_agent
