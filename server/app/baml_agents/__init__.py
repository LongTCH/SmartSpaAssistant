from app.baml_agents.memory import memory_agent
from app.baml_agents.message_rewrite import message_rewrite_agent
from app.baml_agents.script_retrieve import (
    ScriptRetrieveAgentDeps,
    script_retrieve_agent,
)
from app.baml_agents.sheet import SheetAgentDeps, SQLExecutionMessage, sheet_agent
from app.baml_agents.sheet_rag import SheetRAGAgentDeps, sheet_rag_agent
from app.baml_agents.synthetic import SyntheticAgentDeps, synthetic_agent
from app.baml_agents.utils import BAMLAgentRunResult, BAMLMessagesTypeAdapter, dump_json
from app.configs.database import with_session
from app.dtos import ScriptChunkDto
from app.repositories import chat_history_repository
from app.services.integrations import script_rag_service
from baml_client.types import BAMLMessage, ScriptRetrieveAgentOutput
from baml_py import Collector
from langfuse.decorators import langfuse_context, observe

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


@observe(as_type="generation", name="agent_system")
async def invoke_agent(user_id, user_input: str) -> str:
    try:
        chat_histories = await with_session(
            lambda session: chat_history_repository.get_latest_chat_histories(
                session, user_id, limit=MAX_HISTORY_MESSAGES
            )
        )
        message_history: list[BAMLMessage] = []
        for message in chat_histories:
            model_message = BAMLMessagesTypeAdapter.validate_json(message.content)
            message_history.extend(model_message)

        collector = Collector(name="baml")
        baml_options = {"collector": collector}

        message_rewrite_agent_output: BAMLAgentRunResult[str] = (
            await message_rewrite_agent.run(user_input, baml_options=baml_options)
        )
        script_chunks: list[ScriptChunkDto] = (
            await script_rag_service.search_script_chunks(
                message_rewrite_agent_output.output, limit=5
            )
        )
        script_context = "\n".join([chunk.chunk for chunk in script_chunks])
        script_retrieve_agent_deps = ScriptRetrieveAgentDeps(
            script_context=script_context
        )
        retrieve_scripts_result: BAMLAgentRunResult[ScriptRetrieveAgentOutput] = (
            await script_retrieve_agent.run(
                user_input,
                message_history=message_history,
                deps=script_retrieve_agent_deps,
                baml_options=baml_options,
            )
        )
        script_context = "\n".join(retrieve_scripts_result.output.pieces_of_information)
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
                script_context=script_context,
            )
            sheet_result: BAMLAgentRunResult[SQLExecutionMessage] = (
                await sheet_agent.run(
                    user_input, deps=sheet_agent_deps, baml_options=baml_options
                )
            )
            rows = sheet_result.output.result
            sheet_context = ""
            if not rows:
                sheet_messages = sheet_result.new_messages
                sheet_rag_agent_deps = SheetRAGAgentDeps(script_context=script_context)
                sheet_rag_result: BAMLAgentRunResult[str] = await sheet_rag_agent.run(
                    user_input,
                    message_history=sheet_messages,
                    deps=sheet_rag_agent_deps,
                    baml_options=baml_options,
                )
                sheet_context = sheet_rag_result.output
            else:
                sheet_context = (
                    "Queried data from the sheet:\n"
                    f"{dump_json(sheet_result.output.result)}\n"
                )

        synthetic_agent_deps = SyntheticAgentDeps(
            script_context=script_context,
            context_memory=memory,
            sheet_context=sheet_context,
        )
        synthetic_result: BAMLAgentRunResult[str] = await synthetic_agent.run(
            user_input,
            message_history=message_history,
            deps=synthetic_agent_deps,
            baml_options=baml_options,
        )

        chat_content = f"Customer: {user_input}\nAssistant: {synthetic_result.output}"
        memory_agent_output = await memory_agent.run(
            chat_content,
            baml_options=baml_options,
        )
        summary = memory_agent_output.output
        await with_session(
            lambda session: chat_history_repository.insert_chat_history(
                session, user_id, synthetic_result.new_messages_json(), summary
            )
        )
        if collector:
            all_logs = collector.logs
            total_input_tokens = 0
            total_output_tokens = 0
            for log in all_logs:
                total_input_tokens += log.usage.input_tokens
                total_output_tokens += log.usage.output_tokens
            langfuse_context.update_current_observation(
                usage_details={
                    "input": total_input_tokens,
                    "output": total_output_tokens,
                },
            )
        return synthetic_result.output
    except Exception as e:
        print(e)
        return "Sorry, I can't answer that question right now."
