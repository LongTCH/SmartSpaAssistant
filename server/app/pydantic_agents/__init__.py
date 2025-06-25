import logfire
from app.configs.database import async_session, with_session
from app.dtos.setting_dtos import SettingDetailsDto
from app.exceptions.custom_exception import ForbiddenError
from app.models import Script
from app.pydantic_agents.info import InfoAgentDeps, info_agent
from app.pydantic_agents.memory import memory_agent
from app.pydantic_agents.synthetic import SyntheticAgentDeps, create_synthetic_agent
from app.pydantic_agents.synthetic_tools import get_all_available_sheets
from app.repositories import (
    chat_history_repository,
    guest_repository,
    script_repository,
)
from app.services import (
    alert_service,
    interest_service,
    script_service,
    setting_service,
)
from app.services.integrations import script_rag_service
from app.utils import asyncio_utils
from app.utils.agent_utils import MessagePart, contains_xml_tags, dump_json_bytes
from app.utils.message_utils import markdown_remove, parse_and_format_message
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
)
from pydantic_ai.usage import UsageLimits

logfire.configure(send_to_logfire=False)
logger = logfire.instrument_pydantic_ai()

SHORT_TERM_MEMORY_LIMIT = 10
OLD_SCRIPTS_LENGTH = 10
REMIND_INTERVAL = 5
OVERLAP_MEMORY_COUNT = 5
UPDATE_GUEST_INFO_INTERVAL = 3


def convert_messages_to_xml(message_histories: list[ModelMessage]) -> str:
    """Chuyển đổi message_histories thành chuỗi XML"""
    xml_messages = []
    for msg in message_histories:
        if isinstance(msg, ModelRequest):
            # User message
            user_content = msg.parts[0].content if msg.parts else ""
            xml_messages.append(f"<user>{user_content}</user>")
        elif isinstance(msg, ModelResponse):
            # Assistant message
            assistant_content = msg.parts[0].content if msg.parts else ""
            xml_messages.append(f"<assistant>{assistant_content}</assistant>")

    return "\n".join(xml_messages)


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
                lambda session: chat_history_repository.get_chat_histories_until_summary(
                    session, user_id, max_limit=SHORT_TERM_MEMORY_LIMIT
                )
            )
            previous_summary_chat_history = None
            if chat_histories and chat_histories[-1].summary:
                # Nếu có summary, lấy message trước đó để làm history
                previous_summary_chat_history = chat_histories.pop()
            # Đảo ngược thứ tự chat_histories để có message mới nhất ở đầu
            chat_histories = chat_histories[::-1]
            message_history: list[ModelMessage] = []
            message_history.append(
                ModelResponse(
                    parts=[
                        TextPart(
                            content=f"Relevant sheets in XML format that help decide if we need to query from sheets. Carefully study the description and column description of each sheet to decide which sheets should be queried.\n{await get_all_available_sheets(None)}"
                        ),
                    ]
                )
            )
            if previous_summary_chat_history:
                # Nếu có summary, thêm nó vào đầu message_history
                message_history.append(
                    ModelResponse(
                        parts=[
                            TextPart(
                                content=f"Summary of previous conversation: {previous_summary_chat_history.summary}"
                            )
                        ]
                    )
                )

            old_script_ids: set[str] = set()
            # Chỉ lấy old_script_ids từ OLD_SCRIPTS_LENGTH message cuối cùng
            old_scripts_histories = (
                chat_histories[-OLD_SCRIPTS_LENGTH:]
                if len(chat_histories) > OLD_SCRIPTS_LENGTH
                else chat_histories
            )
            for message in old_scripts_histories:
                if message.used_scripts:
                    old_script_ids.update(message.used_scripts.split(","))

            if previous_summary_chat_history:
                overlap_chat_histories = await with_session(
                    lambda session: chat_history_repository.get_latest_chat_histories_from_datetime(
                        session,
                        user_id,
                        previous_summary_chat_history.created_at,
                        OVERLAP_MEMORY_COUNT,
                    )
                )
                chat_histories = overlap_chat_histories[::-1] + chat_histories
            # Xây dựng message_history từ toàn bộ chat_histories
            for message in chat_histories:
                model_message = ModelMessagesTypeAdapter.validate_json(message.content)
                message_history.extend(model_message)
            setting_details = await setting_service.get_setting_details(db)
            setting_details = SettingDetailsDto(**setting_details)
            scripts: list[Script] = (
                await script_rag_service.search_script_chunks(
                    user_input, limit=setting_details.max_script_retrieval
                )
            )[::-1]
            script_ids = [script.id for script in scripts]
            script_ids_in_old_but_not_in_new = old_script_ids - set(script_ids)
            if script_ids_in_old_but_not_in_new:
                scripts.extend(
                    await with_session(
                        lambda db: script_repository.get_scripts_by_ids(
                            db, script_ids_in_old_but_not_in_new
                        )
                    )
                )

            if scripts:
                script_context = await script_service.agent_scripts_to_xml(scripts)
            else:
                script_context = ""
            # Lấy history_count hiện tại để kiểm tra có nên lấy summary không
            latest_count = await chat_history_repository.get_latest_history_count(
                db, user_id
            )

            synthetic_agent_deps = SyntheticAgentDeps(
                user_input=user_input, user_id=user_id
            )
            assistant_messages = []
            if script_context:
                assistant_messages.append(
                    ModelResponse(
                        parts=[
                            TextPart(
                                content=f"Related scripts in XML format. Important information needs to be reranked and filtered to answer the customer.\n{script_context}"
                            ),
                        ]
                    )
                )

            assistant_messages.append(
                ModelResponse(
                    parts=[
                        TextPart(
                            content="""
## PERSISTENCE
You are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.

## PLANNING
You MUST plan extensively before each function call, and reflect extensively on the outcomes of the previous function calls.
"""
                        ),
                    ]
                )
            )

            synthetic_agent = await create_synthetic_agent(user_id)
            synthetic_result = await synthetic_agent.run(
                user_input,
                message_history=message_history + assistant_messages,
                deps=synthetic_agent_deps,
                usage_limits=UsageLimits(request_limit=10, total_tokens_limit=100000),
            )
            agent_output_str = synthetic_result.output
            # Làm sạch output để loại bỏ các thẻ XML có thể bị lộ do prompt injection
            if contains_xml_tags(agent_output_str):
                raise ForbiddenError("Phát hiện nguy hiểm khai thác dữ liệu")
            agent_output_str = markdown_remove(agent_output_str)

            # Xử lý message_parts để đảm bảo media parts chỉ chứa URL và tách riêng text mô tả
            message_parts = parse_and_format_message(agent_output_str)

            # Typically [HumanMessage, AIMessage] or similar
            # agent_new_messages = synthetic_result.new_messages()
            # request_timestamp = (
            #     agent_new_messages[0].parts[0].timestamp
            #     if agent_new_messages
            #     else datetime.datetime.now().isoformat()
            # )

            # get all object of type ModelResponse in agent_new_messages
            # agent_new_responses = [
            #     msg for msg in agent_new_messages if isinstance(msg, ModelResponse)
            # ]

            # Construct current turn's messages in the desired ModelRequest/ModelResponse format
            # current_turn_interaction_objects = [
            #     ModelRequest(
            #         parts=[
            #             UserPromptPart(content=user_input,
            #                            timestamp=request_timestamp)
            #         ]
            #     ),
            # ] + agent_new_responses
            # current_turn_bytes = dump_json_bytes(
            #     current_turn_interaction_objects
            # )
            current_qa_content_str = "".join(
                [
                    f"<user>{user_input}</user>\n",
                    f"<assistant>{synthetic_result.output}</assistant>\n",
                ]
            )
            current_qa_content_bytes = dump_json_bytes(current_qa_content_str)
            script_ids_str = ",".join(script_ids)

            next_count = latest_count + 1
            if next_count > 0 and next_count % UPDATE_GUEST_INFO_INTERVAL == 0:
                asyncio_utils.run_background(
                    run_info_agent_background, user_id, current_qa_content_str
                )

            # Mỗi SHORT_TERM_MEMORY_LIMIT messages tạo summary
            if next_count > 0 and next_count % SHORT_TERM_MEMORY_LIMIT == 0:
                asyncio_utils.run_background(
                    run_memory_with_summary,
                    user_id,
                    synthetic_result.new_messages_json(),
                    script_ids_str,
                    current_qa_content_str,
                    current_qa_content_bytes,
                )
            else:
                # Lưu message mà không tạo summary
                asyncio_utils.run_background(
                    save_message_without_summary,
                    user_id,
                    synthetic_result.new_messages_json(),
                    script_ids_str,
                    current_qa_content_bytes,
                )

            return message_parts
        except ForbiddenError as e:
            print(e)
            await alert_service.insert_system_alert(db, user_id, f"{e.message}")
            return [
                MessagePart(
                    type="text", payload="Xin lỗi, tôi không thể xử lí yêu cầu này."
                )
            ]
        except Exception as e:
            print(e)
            await alert_service.insert_system_alert(
                db, user_id, f"Hệ thống bị lỗi khi cố gắng tạo phản hồi cho khách hàng"
            )
            return [MessagePart(type="text", payload="Xin lỗi, vui lòng thử lại sau")]


async def run_memory_with_summary(
    user_id,
    new_messages,
    script_ids,
    current_qa_content_str,
    current_qa_content_bytes: bytes = None,
):
    """Chạy memory agent và tạo summary cho 10 messages gần nhất"""
    async with async_session() as session:
        list_qa_content_bytes = await with_session(
            lambda session: chat_history_repository.get_latest_qa_content(
                session, user_id, limit=SHORT_TERM_MEMORY_LIMIT
            )
        )
        list_qa_content_str = [byte.decode("utf-8") for byte in list_qa_content_bytes]
        list_qa_content_str.reverse()
        qa_content_histories = "".join(list_qa_content_str).strip('"')
        qa_content_histories = qa_content_histories + f"\n{current_qa_content_str}"
        memory_agent_output = await memory_agent.run(
            f"Below are the conversation messages that need summarization:\n{qa_content_histories}"
        )
        summary = memory_agent_output.output

        # Lưu message hiện tại với summary
        chat_history = await chat_history_repository.insert_chat_history(
            session,
            user_id,
            new_messages,
            summary,
            script_ids,
            current_qa_content_bytes,
        )
        await session.commit()


async def save_message_without_summary(
    user_id, new_messages, script_ids, current_qa_content_bytes: bytes = None
):
    """Lưu message mà không tạo summary"""
    async with async_session() as session:
        await chat_history_repository.insert_chat_history_without_summary(
            session, user_id, new_messages, script_ids, current_qa_content_bytes
        )
        await session.commit()


async def run_info_agent_background(user_id: str, current_qa_content_str: str = None):
    """Chạy info agent trong background để cập nhật thông tin khách hàng"""
    try:
        list_qa_content_bytes = await with_session(
            lambda session: chat_history_repository.get_latest_qa_content(
                session, user_id, limit=SHORT_TERM_MEMORY_LIMIT
            )
        )
        list_qa_content_str = [byte.decode("utf-8") for byte in list_qa_content_bytes]
        list_qa_content_str.reverse()
        qa_content_str = "".join(list_qa_content_str).strip('"')
        if current_qa_content_str:
            qa_content_str += f"\n{current_qa_content_str}"
        if not qa_content_str:
            return
        info_agent_deps = InfoAgentDeps(user_id=user_id)
        await info_agent.run(
            qa_content_str,
            usage_limits=UsageLimits(request_limit=5, total_tokens_limit=100000),
            deps=info_agent_deps,
        )
    except Exception as e:
        print(f"Error running info agent for user {user_id}: {e}")
