from app.baml_agents.master import MasterAgentDeps, master_agent
from app.baml_agents.memory import memory_agent
from app.baml_agents.message_rewrite import message_rewrite_agent
from app.baml_agents.utils import BAMLAgentRunResult, BAMLMessagesTypeAdapter, dump_json
from app.configs.database import with_session
from app.dtos import ScriptChunkDto
from app.repositories import chat_history_repository
from app.services.integrations import script_rag_service
from baml_client.types import BAMLMessage, ChatResponseItem
from baml_py import Collector
from langfuse.decorators import observe

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


@observe(as_type="generation", name="agent_system")
async def invoke_agent(user_id, user_input: str) -> list[ChatResponseItem]:
    try:
        chat_histories = await with_session(
            lambda session: chat_history_repository.get_latest_chat_histories(
                session, user_id, limit=MAX_HISTORY_MESSAGES
            )
        )
        # reverse the order of chat histories
        chat_histories = chat_histories[::-1]
        message_history: list[BAMLMessage] = []
        for message in chat_histories:
            model_message = BAMLMessagesTypeAdapter.validate_json(message.content)
            message_history.extend(model_message)
        collector = Collector(name="baml")
        baml_options = {"collector": collector}

        message_rewrite_agent_output: BAMLAgentRunResult[str] = (
            await message_rewrite_agent.run(user_input, baml_options=baml_options)
        )
        user_input = message_rewrite_agent_output.output
        script_chunks: list[ScriptChunkDto] = (
            await script_rag_service.search_script_chunks(user_input, limit=5)
        )
        script_context = "\n".join([chunk.chunk for chunk in script_chunks])
        # script_retrieve_agent_deps = ScriptRetrieveAgentDeps(
        #     script_context=script_context
        # )
        # retrieve_scripts_result: BAMLAgentRunResult[ScriptRetrieveAgentOutput] = (
        #     await script_retrieve_agent.run(
        #         user_input,
        #         message_history=message_history,
        #         deps=script_retrieve_agent_deps,
        #         baml_options=baml_options,
        #     )
        # )
        # message_history.extend(retrieve_scripts_result.new_messages)
        # script_context = "\n".join(retrieve_scripts_result.output.pieces_of_information)
        # sheet_guard_agent_deps = SheetGuardAgentDeps(
        #     script_context=script_context,
        # )
        # sheet_guard_agent_result: BAMLAgentRunResult[SheetGuardAgentOutput] = (
        #     await sheet_guard_agent.run(
        #         user_input,
        #         deps=sheet_guard_agent_deps,
        #         baml_options=baml_options,
        #     )
        # )
        # should_query_sheet = retrieve_scripts_result.output.should_query_sheet

        chat_summaries = await with_session(
            lambda db: chat_history_repository.get_long_term_memory(
                db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
            )
        )
        memory = "\n".join(chat_summaries)

        # if should_query_sheet:
        #     rows = None
        #     sheet_id = None
        #     limit = None
        #     try:
        #         sheet_agent_deps = SheetAgentDeps(
        #             script_context=script_context,
        #         )
        #         sheet_result: BAMLAgentRunResult[SQLExecutionMessage] = (
        #             await sheet_agent.run(
        #                 user_input,
        #                 deps=sheet_agent_deps,
        #                 message_history=message_history,
        #                 baml_options=baml_options,
        #             )
        #         )
        #         message_history.extend(sheet_result.new_messages)
        #         rows = sheet_result.output.result
        #         sheet_id = sheet_result.output.sheet_id
        #         limit = sheet_result.output.limit
        #     except Exception as e:
        #         pass
        #     sheet_context = ""

        #     if not rows:
        #         # sheet_messages = sheet_result.new_messages
        #         # sheet_rag_agent_deps = SheetRAGAgentDeps(
        #         #     script_context=script_context)
        #         # sheet_rag_result: BAMLAgentRunResult[list[str]] = await sheet_rag_agent.run(
        #         #     user_input,
        #         #     message_history=sheet_messages,
        #         #     deps=sheet_rag_agent_deps,
        #         #     baml_options=baml_options,
        #         # )
        #         # rag_items = sheet_rag_result.output
        #         rag_items = await sheet_rag_service.search_chunks_by_sheet_id(
        #             sheet_id=sheet_id,
        #             query=user_input,
        #             limit=limit,
        #         )
        #         rag_items = [rag_item.chunk for rag_item in rag_items]
        #         sheet_rag_guard_agent_deps = SheetRAGGuardAgentDeps(
        #             script_context="",
        #             rag_items=rag_items,
        #         )
        #         sheet_rag_guard_result: BAMLAgentRunResult[str] = (
        #             await sheet_rag_guard_agent.run(
        #                 user_input,
        #                 message_history=message_history,
        #                 deps=sheet_rag_guard_agent_deps,
        #                 baml_options=baml_options,
        #             )
        #         )
        #         message_history.extend(sheet_rag_guard_result.new_messages)
        #         sheet_context = sheet_rag_guard_result.output
        #     else:
        #         sheet_context = "Queried data from the sheet:\n"
        #         for row in rows:
        #             sheet_context += "\n".join(
        #                 [f"{key}: {value}" for key, value in row.items()]
        #             )
        #             sheet_context += (
        #                 "\n----------------------------------------------\n"
        #             )

        # synthetic_agent_deps = SyntheticAgentDeps(
        #     script_context="",
        #     context_memory=memory,
        #     sheet_context="",
        # )
        # synthetic_result: BAMLAgentRunResult[list[ChatResponseItem]] = (
        #     await synthetic_agent.run(
        #         user_input,
        #         message_history=message_history,
        #         deps=synthetic_agent_deps,
        #         baml_options=baml_options,
        #     )
        # )
        master_agent_deps = MasterAgentDeps(
            script_context=script_context, context_memory=memory
        )
        master_result: BAMLAgentRunResult[list[ChatResponseItem]] = (
            await master_agent.run(
                user_input,
                message_history=message_history,
                deps=master_agent_deps,
                baml_options=baml_options,
            )
        )
        chat_content = (
            f"Customer: {user_input}\nAssistant: {dump_json(master_result.output)}"
        )
        memory_agent_output = await memory_agent.run(
            chat_content,
            baml_options=baml_options,
        )
        summary = memory_agent_output.output
        await with_session(
            lambda session: chat_history_repository.insert_chat_history(
                session, user_id, master_result.new_messages_json(), summary
            )
        )
        # if collector:
        #     all_logs = collector.logs
        #     total_input_tokens = 0
        #     total_output_tokens = 0
        #     for log in all_logs:
        #         total_input_tokens += log.usage.input_tokens
        #         total_output_tokens += log.usage.output_tokens
        #     langfuse_context.update_current_observation(
        #         usage_details={
        #             "input": total_input_tokens,
        #             "output": total_output_tokens,
        #         },
        #     )
        return master_result.output
    except Exception as e:
        print(e)
        return "Sorry, I can't answer that question right now."
