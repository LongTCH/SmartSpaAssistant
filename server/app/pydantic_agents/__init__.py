import logfire
from app.configs.database import async_session, with_session
from app.models import Script
from app.pydantic_agents.memory import MemoryAgentDeps, memory_agent
from app.pydantic_agents.synthetic import SyntheticAgentDeps, create_synthetic_agent
from app.repositories import chat_history_repository, guest_repository
from app.services import chat_history_service, interest_service, script_service
from app.services.integrations import script_rag_service
from app.utils import asyncio_utils
from app.utils.agent_utils import MessagePart
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

logfire.configure(send_to_logfire="if-token-present")
logger = logfire.instrument_pydantic_ai()

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50
SUMMARY_FOR_REWRITE = 5
OLD_MEMORY_LENGTH_FOR_UPDATE_MEMORY = 10


async def invoke_agent(user_id, user_input: str) -> list[MessagePart]:
    async with async_session() as db:
        try:
            interest_ids = await interest_service.get_interest_ids_from_text(
                db, user_input
            )
            await guest_repository.add_interests_to_guest_by_id(
                db, user_id, interest_ids
            )
            await db.commit()

            chat_histories = await with_session(
                lambda session: chat_history_repository.get_latest_chat_histories(
                    session, user_id, limit=MAX_HISTORY_MESSAGES
                )
            )
            chat_histories = chat_histories[::-1]
            message_history: list[ModelMessage] = []
            for message in chat_histories:
                model_message = ModelMessagesTypeAdapter.validate_json(message.content)
                message_history.extend(model_message)

            # message_rewrite_summaries = await with_session(
            #     lambda db: chat_history_repository.get_long_term_memory(
            #         db, user_id, skip=0, limit=SUMMARY_FOR_REWRITE
            #     )
            # )
            # message_rewrite_deps = MessageRewriteAgentDeps(
            #     summaries=message_rewrite_summaries
            # )
            # message_rewrite_agent_output: AgentRunResult[str] = (
            #     await message_rewrite_agent.run(user_input, deps=message_rewrite_deps)
            # )
            # user_input = message_rewrite_agent_output.output
            scripts: list[Script] = await script_rag_service.search_script_chunks(
                user_input, limit=5
            )
            script_context = await script_service.agent_scripts_to_xml(scripts)

            chat_summaries = await with_session(
                lambda db: chat_history_repository.get_long_term_memory(
                    db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
                )
            )
            memory = "\n".join(chat_summaries)

            synthetic_agent_deps = SyntheticAgentDeps(
                user_input=user_input,
                user_id=user_id,
                script_context=script_context,
                context_memory=memory,
            )
            synthetic_agent = await create_synthetic_agent(user_id)
            synthetic_result = await synthetic_agent.run(
                user_input, message_history=message_history, deps=synthetic_agent_deps
            )

            message_parts = synthetic_result.output

            chat_content = await chat_history_service.agent_messages_to_xml(
                user_input, message_parts
            )
            asyncio_utils.run_background(
                run_memory, user_id, chat_content, synthetic_result.new_messages_json()
            )

            return message_parts
        except Exception as e:
            print(e)
            return [MessagePart(type="text", payload="Xin lỗi, vui lòng thử lại sau")]


async def run_memory(user_id, chat_content, new_messages):
    async with async_session() as session:
        summaries = await chat_history_repository.get_long_term_memory(
            session, user_id, skip=0, limit=OLD_MEMORY_LENGTH_FOR_UPDATE_MEMORY
        )
        memory_agent_output = await memory_agent.run(
            chat_content, deps=MemoryAgentDeps(summaries=summaries)
        )
        summary = memory_agent_output.output
        await chat_history_repository.insert_chat_history(
            session, user_id, new_messages, summary
        )
        await session.commit()
