from agents import Runner
from agents.result import RunResult
from app.configs.database import with_session
from app.openai_agents.synthetic import synthetic_agent
from app.openai_agents.utils import OpenAIMessagesTypeAdapter, OpenAIModelMessage
from app.repositories import chat_history_repository

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


async def invoke_agent(user_id, user_input: str) -> str:
    try:
        chat_histories = await with_session(
            lambda session: chat_history_repository.get_latest_chat_histories(
                session, user_id, limit=MAX_HISTORY_MESSAGES
            )
        )
        chat_histories = chat_histories[::-1]
        message_history: list[OpenAIModelMessage] = []
        for message in chat_histories:
            model_message = OpenAIMessagesTypeAdapter.validate_json(message.content)
            message_history.extend(model_message)
        new_user_message = {
            "content": user_input,
            "role": "user",
        }
        message_history.append(new_user_message)
        result: RunResult = await Runner.run(
            starting_agent=synthetic_agent, input=message_history
        )

        new_messages = result.new_items
        new_messages = [new_user_message] + [
            item.to_input_item() for item in new_messages
        ]
        # user_input = message_rewrite_agent_output.output
        # script_chunks: list[ScriptChunkDto] = (
        #     await script_rag_service.search_script_chunks(user_input, limit=5)
        # )
        # script_context = "\n".join([chunk.chunk for chunk in script_chunks])
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

        # chat_summaries = await with_session(
        #     lambda db: chat_history_repository.get_long_term_memory(
        #         db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
        #     )
        # )
        # memory = "\n".join(chat_summaries)

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

        # synthetic_agent_deps = SyntheticAgentDeps(
        #     user_input=user_input,
        #     user_id=user_id,
        #     script_context=script_context,
        #     context_memory=memory,
        # )
        # synthetic_result = await synthetic_agent.run(
        #     user_input, message_history=message_history, deps=synthetic_agent_deps
        # )
        # message_split_result = await message_split_agent.run(
        #     f"{synthetic_result.output}"
        # )
        # chat_content = f"Customer: {user_input}\nAssistant: {synthetic_result.output}"

        # memory_agent_output = await memory_agent.run(chat_content)
        # summary = memory_agent_output.output
        # await with_session(
        #     lambda session: chat_history_repository.insert_chat_history(
        #         session, user_id, retrieve_scripts_result.new_messages_json(), summary
        #     )
        # )
        # await with_session(
        #     lambda session: chat_history_repository.insert_chat_history(
        #         session, user_id, dump_json(new_messages), "summary"
        #     )
        # )

        return result.final_output
    except Exception as e:
        print(e)
        return "Sorry, I can't answer that question right now."
