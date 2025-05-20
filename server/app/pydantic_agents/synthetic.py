import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pytz
from app.configs.database import async_session, with_session
from app.pydantic_agents.model_hub import model_hub
from app.repositories import notification_repository, sheet_repository
from app.services import alert_service, sheet_service
from app.services.integrations import sheet_rag_service
from app.utils.agent_utils import (
    CurrentTimeResponse,
    MessagePart,
    is_read_only_sql,
    normalize_postgres_query,
    normalize_tool_name,
)
from fuzzywuzzy import process
from jinja2 import Environment, FileSystemLoader
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.tools import ToolDefinition
from sqlalchemy import text


@dataclass
class SyntheticAgentDeps:
    user_input: str
    user_id: str
    script_context: str
    context_memory: str
    timezone: str = "Asia/Ho_Chi_Minh"


# instructions = """
#     From provided context and sheet description, decide whether you should query from the sheet or prompt customer for more information.
#     Think carefully when query from the sheet without LIMIT clause, it may return too much data. If information has provided in the context, you should not query from the sheet.
#     If you need to query from the sheet, carefully analyze the customer's message, provided context, the sheet description and column description to construct the SQL query.
# """


async def get_current_local_time(
    context: RunContext[SyntheticAgentDeps],
) -> CurrentTimeResponse:
    """
    Get the current local time (ISO Format) at local timezone.
    """
    tz = pytz.timezone(context.deps.timezone)
    local_time = datetime.now(tz)
    return CurrentTimeResponse(
        timezone=context.deps.timezone,
        current_time=local_time.isoformat(),
    )


async def rag_hybrid_search(sheet_id: str, query: str, limit: int) -> list[str]:
    """
    Only use this tool if cannot find the data from SQL query.
    Use this tool to query from the RAG (Retrieval-Augmented Generation) database.
    Sparse vector (BM25) captures exact keyword matches and term importance based on token frequency.
    It is effective for precise matches on specific terms or phrases.

    Results are returned as a list of text entries. Each entry represents a row from a knowledge sheet
    identified by 'sheet.id' in the 'sheet' table of database.
    Use this tool when SQL tool not returning appropriate data.

    Args:
        sheet_id: The ID of the sheet to query.
        query: The query string to search for.
        limit: The maximum number of results to return.
    """
    # replace _ to - in sheet_id
    sheet_id = sheet_id.replace("_", "-")
    sheets = await with_session(
        lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
    )
    sheet_ids = [sheet.id for sheet in sheets]
    if sheet_id not in sheet_ids:
        best_id, score = process.extractOne(sheet_id, sheet_ids)
        if score < 60:
            raise ModelRetry(
                f"Invalid sheet_id: {sheet_id}. "
                f"Best match '{best_id}' has only {score} points."
            )
        sheet_id = best_id

    sheet_chunks = await sheet_rag_service.search_chunks_by_sheet_id(
        sheet_id=sheet_id,
        query=query,
        limit=limit,
    )
    return [sheet_chunk.chunk for sheet_chunk in sheet_chunks]


async def get_all_available_sheets() -> str:
    """
    Get all available sheets in XML Format from the database to analyze structure in order to construct sql query.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        if not sheets:
            return ""
        context = (
            "Here is relevant sheets in XML Format that help you to decide if we need query from sheets:\n"
            "Carefully study the description description and column description of each sheet.\n"
        )
        context += await sheet_service.agent_sheets_to_xml(sheets)
        # sheet_list = [
        #     {
        #         "id": sheet.id,
        #         "name": sheet.name,
        #         "description": sheet.description,
        #         "column_config": sheet.column_config,
        #         "table_name": sheet.table_name,
        #     }
        #     for sheet in sheets
        # ]
        # for i, sheet in enumerate(sheets):
        #     example_rows = await with_session(
        #         lambda session: sheet_repository.get_example_rows_by_sheet_id(
        #             session, sheet.id
        #         )
        #     )
        #     # Convert SQLAlchemy RowMapping objects to dictionaries
        #     example_rows_dict = []
        #     for row in example_rows:
        #         example_rows_dict.append(dict(row))
        #     sheet_list[i]["example_rows"] = limit_sample_rows_content(
        #         example_rows_dict, 255
        #     )

        return context
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


async def execute_query_on_sheet_rows(
    explain: str, sql_query: str
) -> list[dict[str, any]]:
    """
    Use this tool to query from {sheet.table_name} when you know the table_name via the sheet you are querying. FROM "{sheet.table_name}" is the table name you need to query from.
    You can use other fields of {table_name} specified in {sheet.column_config}, with normal operations to filter the query.
    You should use &@~ instead of = ,LIKE, ILIKE against string, text field of "{sheet.table_name}" to perform fulltext search, examine 'sheet.column_config' field of that sheet in 'sheets' table to know about these columns.
    In SQL, the correct order of statement is:
    SELECT …
    FROM …
    [WHERE …]
    [GROUP BY …]
    [HAVING …]
    [ORDER BY …]
    [LIMIT …];

    NOTICE: The table to query FROM is "{sheet.table_name}".
    Prefer using normal sql query to filter the data.
    You must enclose the table name, column names, keywords in fulltext search in double quotes.
    Dont use single quotes for table name and column names.

    For example:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE "product_price" > 100

    How to use PGroonga for text fields
    &@~ operator
    You can use &@~ operator to perform full text search by query syntax such as "keyword1" OR "keyword2":

    SELECT * FROM memos WHERE content &@~ '"PGroonga" OR "PostgreSQL"';
    --  id |                            content
    -- ----+----------------------------------------------------------------
    --   3 | PGroonga is a PostgreSQL extension that uses Groonga as index.
    --   1 | PostgreSQL is a relational database management system.
    -- (2 rows)
    Query syntax ( "keyword1" OR "keyword2" ) means OR search and ( "keyword1" "keyword2" ) means AND search.
    You must always enclose the pgroonga query in parentheses, for example: FROM "some_table_name" WHERE ("some_column" &@~ '"keyword1" OR "keyword2")​

    Example 1:
    If the input keyword string is: "tàn nhang"
    Then the SQL query should be:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE ("description" &@~ '"tàn nhang"')

    Normal query without fulltext search.
    Example 2:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name" as tb
    WHERE tb."product_price" > 100

    Args:
        explain: The detailed explaination of the sql_query.
        sql_query: The PostgreSQL valid query string to search for.
    """
    try:
        async with async_session() as db:
            query = normalize_postgres_query(sql_query)
            if not is_read_only_sql(query):
                raise ModelRetry(
                    "Query must be read-only SQL. Please check your query again."
                )
            sheets = await sheet_repository.get_all_sheets_by_status(db, "published")
            table_names = [sheet.table_name for sheet in sheets]
            query = replace_table_if_needed(query, table_names)
            # execute the query and return the result
            result = await db.execute(text(query))
            # Fetch all results as dictionaries
            rows = result.mappings().all()
            # if rows is empty, raise ModelRetry
            if not rows:
                raise ModelRetry(
                    "No data found. Please check your query again."
                    "If your query contain fulltext search, such as data &@~ 'example keyword', that will search rows contain both 'example' and 'keyword'."
                    "Prefer using less keywords or using OR to comine them. Please check your keywords."
                )
            return [dict(row) for row in rows]
    except ModelRetry as model_retry:
        raise model_retry
    except Exception as e:
        print(f"Error executing query: {e}")
        raise ModelRetry(
            f"Error executing query: {str(e)}. Please reanalyze sheets structure using `get_all_available_sheets` tool."
        )


def get_type_from_param_type(param_type: str) -> str:
    if param_type == "String":
        return "string"
    elif param_type == "Numeric":
        return "number"
    elif param_type == "Boolean":
        return "boolean"
    elif param_type == "DateTime":
        return "string"
    elif param_type == "Integer":
        return "integer"
    return "string"


def get_description_from_param(param_type: str, description: str) -> str:
    if param_type == "DateTime":
        return description + " FORMAT: YYYY-MM-DD HH:MM:SS"
    return description


def create_tool(notification_id: str, guest_id: str, tool_info: Dict[str, Any]) -> Tool:
    async def tool_function(**kwargs):
        empty_params = []
        # loop all params in kwargs to check find all empty params
        for param_name in tool_info["parameters"]["properties"]:
            if param_name not in kwargs or not kwargs[param_name]:
                empty_params.append(param_name)
        if empty_params:
            raise ModelRetry(
                f"Missing required parameters, can't not send notification now: {', '.join(empty_params)}"
            )
        return await alert_service.agent_insert_alert(
            notification_id=notification_id, guest_id=guest_id, **kwargs
        )

    this_tool_def = ToolDefinition(
        name=tool_info["name"],
        description=tool_info["description"],
        parameters_json_schema=tool_info["parameters"],
    )

    async def prepare_tool(ctx, tool_def: ToolDefinition):
        return this_tool_def

    tool = Tool(
        name=tool_info["name"],
        description=tool_info["description"],
        prepare=prepare_tool,
        takes_ctx=False,
        function=tool_function,
    )
    return tool


async def get_instruction(context: RunContext[SyntheticAgentDeps]) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Tạo Jinja environment từ thư mục đó
    env = Environment(loader=FileSystemLoader(current_dir))

    # Load template
    template = env.get_template("synthetic_prompt.j2")
    rendered = template.render(
        memory_context=context.deps.context_memory,
        scripts_context=context.deps.script_context,
        sheets_context=await get_all_available_sheets(),
    )
    return rendered


async def create_synthetic_agent(
    guest_id: str,
) -> Agent[SyntheticAgentDeps, list[MessagePart]]:
    extra_tools_json = []
    all_notifications = await with_session(
        lambda db: notification_repository.get_all_notifications_by_status(
            db, "published"
        )
    )
    for notification in all_notifications:
        tool_json = {
            "notification_id": notification.id,
            "name": normalize_tool_name("send_notify_" + notification.label),
            "description": f"Call this tool in case: {notification.description}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
        for param in notification.params:
            tool_json["parameters"]["properties"][param["param_name"]] = {
                "type": get_type_from_param_type(param["param_type"]),
                "description": get_description_from_param(
                    param["param_type"], param["description"]
                ),
            }
            tool_json["parameters"]["required"].append(param["param_name"])
        extra_tools_json.append(tool_json)
    extra_tools = [
        create_tool(tool_info["notification_id"], guest_id, tool_info)
        for tool_info in extra_tools_json
    ]

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
        ]
        + extra_tools,
    )

    # @synthetic_agent.system_prompt
    # async def get_characteristics(context: RunContext[SyntheticAgentDeps]) -> str:
    #     return """
    #     CHARACTERISTICS:
    #     You are Nguyen Thi Phuong Thao, a 25‑year‑old female customer service specialist at Mailisa Spa (skin care). You are dynamic, polite, supportive, well‑explained, and soft‑spoken. Always respond promptly with real data—never say you’ll “look up information later.”
    #     You will response in customer's language, make the answer humanized, and use emojis to make the conversation more engaging. You are not a bot, so avoid using technical terms or jargon.
    #     BEHAVIOR:
    #     1. Just provide information from trusted context. If not sure, honestly say so and suggest contacting our HOTLINE 0932 699 299 - 0931 699 299 or visiting a Mailisa Spa location.
    #     2. Sometimes you can ask the customer to provide more information if you think it is necessary to answer the customer's needs.
    #     3. Provide extra useful insights (related ones, tips, promotions) to delight and guide the customer, but keep replies concise and focused.
    #     4. Limit the use of emojis to 2-3 per message. Use them to enhance the message, not to clutter it.
    #     5. **Important Output Formatting:** Your response will be structured as a list of `MessagePart` objects. If your complete answer is long (e.g., would naturally exceed 50 words), you **MUST** divide it into multiple, logically connected `MessagePart` objects. Each individual `MessagePart` in the list should have its `payload` (the text content) be less than 50 words. For instance, a 120-word answer should result in a list containing approximately three `MessagePart` objects, each with a payload under 50 words. Group related information into sequential messages to maintain coherence.
    #     GOAL:
    #     Deliver trusted, accurate, engaging, and value‑added answers that showcase Mailisa’s expertise and encourage customers to book treatments or purchase products.
    # """

    # @synthetic_agent.system_prompt
    # async def get_tools(context: RunContext[SyntheticAgentDeps]) -> str:
    #     """
    #     Get all tools.
    #     """
    #     return """
    #     You are provided with these tools:
    #     1. `get_all_available_sheets`: Use this tool to get all available sheets from the database to analyze structure in order to construct sql query.

    #     2. `execute_query_on_sheet_rows`: Use this tool to query from sheet.table_name when you know the table_name via the sheet you are querying. FROM "sheet.table_name" is the table name you need to query from.
    #     From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description, example data.
    #     After analyzing the sheets, you can write sql query and use the `execute_query_on_sheet_rows` tool to query the sheet data. Do not return sql query in final response.

    #     3. `rag_hybrid_search`: Use this tool to query from the RAG (Retrieval-Augmented Generation) database.
    #     You are also provided with the RAG tool to query vector database, each vector contains an entire row of sheet.
    #     If query SQL not return data, you can fall back to RAG tool, but notice that results from RAG are just relevant data and not the accurate data.

    #     4. Multiple tools with name as `send_notify_{notification.label}` and description as `Call this tool in case: {notification.description}`
    #     Before responding to the customer, you need to check whether we need to call any or many of these tools to notify our admin.
    #     Please check the description of each tool to see when to call them.

    #     5. `get_current_local_time`: Use this tool to get the current local time (ISO Format) at local timezone.
    #     """

    # @synthetic_agent.system_prompt
    # async def get_context_memory(context: RunContext[SyntheticAgentDeps]) -> str:
    #     """
    #     Get context memory from the database.
    #     """
    #     context = context.deps.context_memory
    #     if not context:
    #         return ""
    #     return f"\n## Relevant information from previous conversations:\n{context}"

    # @synthetic_agent.system_prompt
    # async def get_all_associated_scripts(
    #     context: RunContext[SyntheticAgentDeps],
    # ) -> str:
    #     """
    #     Get all associated scripts from the database.
    #     """
    #     script_context = context.deps.script_context
    #     if not script_context:
    #         return ""
    #     return f"\n## Here are related instructions. You need to rerank and filter important ones:\n{script_context}\n"

    # @synthetic_agent.system_prompt
    # async def get_sheet_context(
    #     context: RunContext[SyntheticAgentDeps],
    # ) -> str:
    #     return await get_all_available_sheets()

    return synthetic_agent


def get_table_name_from_query(query: str) -> str:
    """
    Extract table name after FROM clause, handling both single and double quotes.
    """
    # Try to find table name in double quotes first
    match = re.search(r'FROM\s+"([^"]+)"', query, re.IGNORECASE)
    if match:
        return match.group(1)

    # If not found, try with single quotes
    match = re.search(r"FROM\s+'([^']+)'", query, re.IGNORECASE)
    if match:
        return match.group(1)

    # If still not found, try without quotes
    match = re.search(r"FROM\s+([a-zA-Z0-9_]+)", query, re.IGNORECASE)
    if match:
        return match.group(1)

    raise ModelRetry("Could not find table name in query.")


def replace_table_if_needed(
    query: str, available_table_names: list[str], min_score: int = 60
) -> str:
    # Extract table name from query
    try:
        table_in_query = get_table_name_from_query(query)
    except ModelRetry:
        # If we can't extract the table name, return the query unchanged
        return query

    # If table name is not in the list, find and replace
    if table_in_query not in available_table_names:
        best_table, score_table = process.extractOne(
            table_in_query, available_table_names
        )
        if score_table < min_score:
            raise ModelRetry(
                f"Invalid table name: {table_in_query}. "
                f"Best match '{best_table}' has only {score_table} points."
            )

        # Replace table name in FROM clause with the best match
        query = query.replace(table_in_query, best_table)

    return query
