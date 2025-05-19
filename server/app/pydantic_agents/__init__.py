import logfire
from app.configs.database import with_session
from app.dtos import ScriptChunkDto
from app.pydantic_agents.memory import memory_agent
from app.pydantic_agents.message_rewrite import message_rewrite_agent
from app.pydantic_agents.synthetic import SyntheticAgentDeps, create_synthetic_agent
from app.repositories import chat_history_repository
from app.services.integrations import script_rag_service
from app.utils import asyncio_utils
from app.utils.agent_utils import MessagePart, dump_json
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

logfire.configure(send_to_logfire="if-token-present")
logger = logfire.instrument_pydantic_ai()

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


async def invoke_agent(user_id, user_input: str) -> list[MessagePart]:
    try:
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
        message_rewrite_agent_output: AgentRunResult[str] = (
            await message_rewrite_agent.run(user_input)
        )
        user_input = message_rewrite_agent_output.output
        script_chunks: list[ScriptChunkDto] = (
            await script_rag_service.search_script_chunks(user_input, limit=5)
        )
        script_context = "\n".join([chunk.chunk for chunk in script_chunks])
        # script_retrieve_agent_deps = ScriptRetrieveAgentDeps(
        #     user_input=user_input, user_id=user_id, script_context=script_context
        # )
        # retrieve_scripts_result: AgentRunResult[ScriptRetrieveAgentOutput] = (
        #     await script_retrieve_agent.run(
        #         user_input,
        #         message_history=message_history,
        #         deps=script_retrieve_agent_deps,
        #     )
        # )
        # message_history.extend(retrieve_scripts_result.new_messages())
        # script_context = "\n".join(
        #     retrieve_scripts_result.output.pieces_of_information)
        # should_query_sheet = retrieve_scripts_result.output.should_query_sheet

        chat_summaries = await with_session(
            lambda db: chat_history_repository.get_long_term_memory(
                db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
            )
        )
        memory = "\n".join(chat_summaries)

        # if should_query_sheet:
        #     sheet_agent_deps = SheetAgentDeps(
        #         user_input=user_input,
        #         user_id=user_id,
        #         script_context=script_context,
        #     )
        #     sheet_result: AgentRunResult = await sheet_agent.run(
        #         user_input, deps=sheet_agent_deps
        #     )
        #     sheet_context = sheet_result.output

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

        chat_content = (
            f"Customer: {user_input}\nAssistant: {dump_json(synthetic_result.output)}"
        )
        asyncio_utils.run_background(
            run_memory, user_id, chat_content, synthetic_result.new_messages_json()
        )

        return synthetic_result.output
    except Exception as e:
        print(e)
        return "Sorry, I can't answer that question right now."


async def run_memory(user_id, chat_content, new_messages):
    memory_agent_output = await memory_agent.run(chat_content)
    summary = memory_agent_output.output
    await with_session(
        lambda session: chat_history_repository.insert_chat_history(
            session, user_id, new_messages, summary
        )
    )
