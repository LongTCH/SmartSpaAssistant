import logfire
from app.agents.memory import memory_agent
from app.agents.script_retrieve import script_retrieve_agent
from app.agents.sheet import SheetAgentDeps, sheet_agent
from app.agents.synthetic import SyntheticAgentDeps, synthetic_agent
from app.configs.database import with_session
from app.repositories import chat_history_repository
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

logfire.configure(send_to_logfire="if-token-present")
logger = logfire.instrument_pydantic_ai()

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


async def invoke_agent(user_id, user_input: str) -> str:
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

        retrieve_scripts_result: AgentRunResult = await script_retrieve_agent.run(
            user_input, message_history=message_history
        )
        script_context = retrieve_scripts_result.output

        chat_summaries = await with_session(
            lambda db: chat_history_repository.get_long_term_memory(
                db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
            )
        )
        memory = "\n".join(chat_summaries)

        sheet_agent_deps = SheetAgentDeps(
            user_input=user_input,
            user_id=user_id,
            script_context=script_context,
            context_memory=memory,
        )
        sheet_result: AgentRunResult = await sheet_agent.run(
            user_input, message_history=message_history, deps=sheet_agent_deps
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
            user_input=user_input,
            message_history=message_history,
            deps=synthetic_agent_deps,
        )

        chat_content = f"Customer: {user_input}\nAssistant: {synthetic_result.output}"
        memory_agent_output = await memory_agent.run(chat_content)
        summary = memory_agent_output.output
        await with_session(
            lambda session: chat_history_repository.insert_chat_history(
                session, user_id, synthetic_result.new_messages_json(), summary
            )
        )

        return synthetic_result.output
    except Exception as e:
        print(e)
        return "Sorry, I can't answer that question right now."
