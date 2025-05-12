import logfire
from app.agents.memory import memory_agent
from app.agents.message_rewrite import message_rewrite_agent
from app.agents.script_retrieve import (
    ScriptRetrieveAgentDeps,
    ScriptRetrieveAgentOutput,
    script_retrieve_agent,
)
from app.agents.sheet import SheetAgentDeps, sheet_agent
from app.agents.synthetic import SyntheticAgentDeps, synthetic_agent
from app.configs.database import with_session
from app.dtos import ScriptChunkDto
from app.repositories import chat_history_repository
from app.services.integrations import script_rag_service
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.usage import UsageLimits

logfire.configure(send_to_logfire="if-token-present")
logger = logfire.instrument_pydantic_ai()

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


async def invoke_agent(user_id, user_input: str) -> str:
    usage_limit_count = 3
    while usage_limit_count > 0:
        try:
            chat_histories = await with_session(
                lambda session: chat_history_repository.get_latest_chat_histories(
                    session, user_id, limit=MAX_HISTORY_MESSAGES
                )
            )
            message_history: list[ModelMessage] = []
            for message in chat_histories:
                model_message = ModelMessagesTypeAdapter.validate_json(message.content)
                message_history.extend(model_message)
            message_rewrite_agent_output: AgentRunResult[str] = (
                await message_rewrite_agent.run(
                    user_input, usage_limits=UsageLimits(request_limit=2)
                )
            )
            script_chunks: list[ScriptChunkDto] = (
                await script_rag_service.search_script_chunks(
                    message_rewrite_agent_output.output, limit=5
                )
            )
            script_context = "\n".join([chunk.chunk for chunk in script_chunks])
            script_retrieve_agent_deps = ScriptRetrieveAgentDeps(
                user_input=user_input, user_id=user_id, script_context=script_context
            )
            retrieve_scripts_result: AgentRunResult[ScriptRetrieveAgentOutput] = (
                await script_retrieve_agent.run(
                    user_input,
                    message_history=message_history,
                    deps=script_retrieve_agent_deps,
                    usage_limits=UsageLimits(request_limit=2),
                )
            )
            script_context = "\n".join(
                retrieve_scripts_result.output.pieces_of_information
            )
            should_query_sheet = retrieve_scripts_result.output.should_query_sheet

            chat_summaries = await with_session(
                lambda db: chat_history_repository.get_long_term_memory(
                    db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
                )
            )
            memory = "\n".join(chat_summaries)

            sheet_context = None
            if should_query_sheet:
                sheet_agent_deps = SheetAgentDeps(
                    user_input=user_input,
                    user_id=user_id,
                    script_context=script_context,
                )
                sheet_result: AgentRunResult = await sheet_agent.run(
                    user_input,
                    deps=sheet_agent_deps,
                    usage_limits=UsageLimits(request_limit=2),
                )
                sheet_context = sheet_result.output

            synthetic_agent_deps = SyntheticAgentDeps(
                user_input=user_input,
                user_id=user_id,
                script_context=script_context,
                context_memory=memory,
                sheet_context=sheet_context,
            )
            synthetic_result: AgentRunResult[str] = await synthetic_agent.run(
                user_input,
                message_history=message_history,
                deps=synthetic_agent_deps,
                usage_limits=UsageLimits(request_limit=2),
            )

            chat_content = (
                f"Customer: {user_input}\nAssistant: {synthetic_result.output}"
            )
            memory_agent_output = await memory_agent.run(
                chat_content, usage_limits=UsageLimits(request_limit=2)
            )
            summary = memory_agent_output.output
            await with_session(
                lambda session: chat_history_repository.insert_chat_history(
                    session, user_id, synthetic_result.new_messages_json(), summary
                )
            )

            return synthetic_result.output
        except UsageLimitExceeded as e:
            usage_limit_count -= 1
        except Exception as e:
            print(e)
            return "Sorry, I can't answer that question right now."
    return "Sorry, I can't answer that question right now."
