import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytz
from agents import (
    Agent,
    ModelSettings,
    RunContextWrapper,
    default_tool_error_function,
    function_tool,
)
from app.configs.database import async_session, with_session
from app.dtos import ScriptChunkDto
from app.repositories import chat_history_repository, sheet_repository
from app.services.integrations import script_rag_service, sheet_rag_service
from app.utils.agent_utils import (
    CurrentTimeResponse,
    MessagePart,
    dump_json,
    is_read_only_sql,
    limit_sample_rows_content,
    normalize_postgres_query,
)
from fuzzywuzzy import process
from sqlalchemy import text

MAX_HISTORY_MESSAGES = 5
LONG_TERM_MEMORY_LIMIT = 50


@dataclass
class SyntheticAgentDeps:
    user_input: str
    user_id: str
    script_context: str
    context_memory: str
    timezone: str = "Asia/Ho_Chi_Minh"


async def get_characteristics(wrapper: RunContextWrapper[SyntheticAgentDeps]) -> str:
    return """
    CHARACTERISTICS:
    You are Nguyen Thi Phuong Thao, a 25‑year‑old female customer service specialist at Mailisa Spa (skin care). You are dynamic, polite, supportive, well‑explained, and soft‑spoken. Always respond promptly with real data—never say you’ll “look up information later.”
    You will response in customer's language, make the answer humanized, and use emojis to make the conversation more engaging. You are not a bot, so avoid using technical terms or jargon.
    BEHAVIOR:
    1. Just provide information from trusted context. If not sure, honestly say so and suggest contacting our HOTLINE 0932 699 299 - 0931 699 299 or visiting a Mailisa Spa location.
    2. Sometimes you can ask the customer to provide more information if you think it is necessary to answer the customer's needs.
    3. Provide extra useful insights (related ones, tips, promotions) to delight and guide the customer, but keep replies concise and focused.
    4. Limit the use of emojis to 2-3 per message. Use them to enhance the message, not to clutter it.
    5. **Important Output Formatting:** Your response will be structured as a list of `MessagePart` objects. If your complete answer is long (e.g., would naturally exceed 50 words), you **MUST** divide it into multiple, logically connected `MessagePart` objects. Each individual `MessagePart` in the list should have its `payload` (the text content) be less than 50 words. For instance, a 120-word answer should result in a list containing approximately three `MessagePart` objects, each with a payload under 50 words. Group related information into sequential messages to maintain coherence.
    GOAL:
    Deliver trusted, accurate, engaging, and value‑added answers that showcase Mailisa’s expertise and encourage customers to book treatments or purchase products.
"""


async def get_tools(wrapper: RunContextWrapper[SyntheticAgentDeps]) -> str:
    """
    Get all tools.
    """
    return """
    You are provided with these tools:
    1. `get_all_available_sheets`: Use this tool to get all available sheets from the database to analyze structure in order to construct sql query.
    
    2. `execute_query_on_sheet_rows`: Use this tool to query from sheet.table_name when you know the table_name via the sheet you are querying. FROM "sheet.table_name" is the table name you need to query from.
    From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description, example data. 
    After analyzing the sheets, you can write sql query and use the `execute_query_on_sheet_rows` tool to query the sheet data. Do not return sql query in final response.
    
    3. `rag_hybrid_search`: Use this tool to query from the RAG (Retrieval-Augmented Generation) database.
    You are also provided with the RAG tool to query vector database, each vector contains an entire row of sheet.
    If query SQL not return data, you can fall back to RAG tool, but notice that results from RAG are just relevant data and not the accurate data.
    
    4. `get_current_local_time`: Use this tool to get the current local time (ISO Format) at local timezone.
    
    5. `get_long_term_memory`: Use this tool to get long term memory from the database.

    6. `get_all_associated_scripts`: Use this tool to get all associated QA scripts for instruction.

    7. `get_all_available_sheets`: Use this tool to get all available sheets from the database to analyze structure in order to construct sql query.
    """


async def get_context_memory(wrapper: RunContextWrapper[SyntheticAgentDeps]) -> str:
    """
    Get long-term memory about current customer from the database.
    Always use this tool for each user input.
    """
    context = wrapper.context.context_memory
    if not context:
        return ""
    return f"\n## Relevant information from previous conversations:\n{context}"


async def get_sheets_desc(wrapper: RunContextWrapper[SyntheticAgentDeps]) -> str:
    """
    Get associated sheet from the database.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        if not sheets:
            return "No available sheets. So set should_query_sheet to False."
        sheets_desc = ""
        for sheet in sheets:
            sheets_desc += (
                f"Sheet name: {sheet.name}\n Sheet description: {sheet.description}\n"
                "----------------------------------\n"
                # "Sheet columns:\n"
            )
            # for column in sheet.column_config:
            #     sheets_desc += (
            #         f"Column name: {column['column_name']}\n"
            #         f"Column description: {column['description']}\n"
            #     )
        return (
            "Here is relevant sheets that help you to decide if we need query from sheets:\n"
            "Carefully study the description description of each sheet.\n"
            f"{sheets_desc}"
        )
    except Exception as e:
        return f"Error fetching sheets: {str(e)}"


instructions = """
    From provided context and sheet description, decide whether you should query from the sheet or prompt customer for more information.
    Think carefully when query from the sheet without LIMIT clause, it may return too much data. If information has provided in the context, you should not query from the sheet.
    If you need to query from the sheet, carefully analyze the customer's message, provided context, the sheet description and column description to construct the SQL query.
"""


async def dynamic_instructions(
    wrapper: RunContextWrapper[SyntheticAgentDeps], agent: Agent[SyntheticAgentDeps]
) -> str:
    characteristics = await get_characteristics(wrapper)
    # script_context = await get_all_associated_scripts(wrapper)
    # current_local_time = await get_current_local_time(wrapper)
    tools_context = await get_tools(wrapper)
    # context_memory = await get_context_memory(wrapper)
    # sheets_desc = await get_sheets_desc(wrapper)
    return (
        instructions
        + characteristics
        # + script_context
        # + current_local_time
        + tools_context
        # + context_memory
        # + sheets_desc
    )


@function_tool(failure_error_function=default_tool_error_function)
async def get_all_associated_scripts(
    wrapper: RunContextWrapper[SyntheticAgentDeps], user_rewrite_input: str
) -> str:
    """
    Pass the rewritten user input to get all associated QA scripts for instruction.
    Always use this tool for each user input.
    """
    script_chunks: list[ScriptChunkDto] = await script_rag_service.search_script_chunks(
        user_rewrite_input, limit=5
    )
    script_context = "\n".join([chunk.chunk for chunk in script_chunks])
    if not script_context:
        return ""
    return f"\n## Here are related instructions. You need to rerank and filter important ones:\n{script_context}\n"


@function_tool(failure_error_function=default_tool_error_function)
async def get_all_available_sheets(
    wrapper: RunContextWrapper[SyntheticAgentDeps],
) -> list[dict[str, Any]]:
    """
    Get all available sheets from the database to analyze structure in order to construct sql query.
    Always use this tool before execute_query_on_sheet_rows tool.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        if not sheets:
            return "No available sheets."
        sheet_list = [
            {
                "id": sheet.id,
                "name": sheet.name,
                "description": sheet.description,
                "column_config": sheet.column_config,
                "table_name": sheet.table_name,
            }
            for sheet in sheets
        ]
        for i, sheet in enumerate(sheets):
            example_rows = await with_session(
                lambda session: sheet_repository.get_example_rows_by_sheet_id(
                    session, sheet.id
                )
            )
            # Convert SQLAlchemy RowMapping objects to dictionaries
            example_rows_dict = []
            for row in example_rows:
                example_rows_dict.append(dict(row))
            sheet_list[i]["example_rows"] = limit_sample_rows_content(example_rows_dict)
        return f"""
            "Here is relevant sheets that help you to decide if we need query from sheets:\n"
            "Carefully study the description description and column description of each sheet.\n"
            {dump_json(sheet_list)}
            """
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


@function_tool(failure_error_function=default_tool_error_function)
async def rag_hybrid_search(
    wrapper: RunContextWrapper[SyntheticAgentDeps],
    sheet_id: str,
    query: str,
    limit: int,
) -> list[str]:
    """
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
            raise Exception(
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


@function_tool(failure_error_function=default_tool_error_function)
async def execute_query_on_sheet_rows(explain: str, query: str) -> list[dict[str, any]]:
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
        explain: The detailed explanation of the query.
        query: The query string to search for.
    """
    try:
        async with async_session() as db:
            query = normalize_postgres_query(query)
            if not is_read_only_sql(query):
                raise Exception(
                    "Query must be read-only SQL. Please check your query again."
                )
            sheets = await sheet_repository.get_all_sheets_by_status(db, "published")
            table_names = [sheet.table_name for sheet in sheets]
            query = replace_table_if_needed(query, table_names)
            # execute the query and return the result
            result = await db.execute(text(query))
            # Fetch all results as dictionaries
            rows = result.mappings().all()
            # if rows is empty, raise Exception
            if not rows:
                raise Exception(
                    "No data found. Please check your query again."
                    "If your query contain fulltext search, such as data &@~ 'example keyword', that will search rows contain both 'example' and 'keyword'."
                    "Prefer using less keywords or using OR to comine them. Please check your keywords."
                )
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error executing query: {e}")
        raise Exception(
            f"Error executing query: {str(e)}. Please check your query again."
        )


@function_tool(failure_error_function=default_tool_error_function)
async def get_current_local_time(
    wrapper: RunContextWrapper[SyntheticAgentDeps],
) -> CurrentTimeResponse:
    """
    Get the current local time (ISO Format) at local timezone.
    """
    tz = pytz.timezone(wrapper.context.timezone)
    local_time = datetime.now(tz)
    return CurrentTimeResponse(
        timezone=wrapper.context.timezone,
        current_time=local_time.isoformat(),
    )


@function_tool(failure_error_function=default_tool_error_function)
async def get_long_term_memory(
    wrapper: RunContextWrapper[SyntheticAgentDeps], user_id: str
) -> str:
    """
    Get long term memory from the database.
    """
    chat_summaries = await with_session(
        lambda db: chat_history_repository.get_long_term_memory(
            db, user_id, skip=MAX_HISTORY_MESSAGES, limit=LONG_TERM_MEMORY_LIMIT
        )
    )
    memory = "\n".join(chat_summaries)
    return (
        f"\n## Here are relevant information from previous conversations:\n{memory}\n"
    )


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

    raise Exception("Could not find table name in query.")


def replace_table_if_needed(
    query: str, available_table_names: list[str], min_score: int = 60
) -> str:
    # Extract table name from query
    try:
        table_in_query = get_table_name_from_query(query)
    except Exception:
        # If we can't extract the table name, return the query unchanged
        return query

    # If table name is not in the list, find and replace
    if table_in_query not in available_table_names:
        best_table, score_table = process.extractOne(
            table_in_query, available_table_names
        )
        if score_table < min_score:
            raise Exception(
                f"Invalid table name: {table_in_query}. "
                f"Best match '{best_table}' has only {score_table} points."
            )

        # Replace table name in FROM clause with the best match
        query = query.replace(table_in_query, best_table)

    return query


synthetic_agent = Agent[SyntheticAgentDeps](
    name="synthetic_agent",
    model="gpt-4o-mini",
    instructions=dynamic_instructions,
    tools=[
        get_all_available_sheets,
        rag_hybrid_search,
        execute_query_on_sheet_rows,
        get_current_local_time,
        get_long_term_memory,
        get_all_associated_scripts,
    ],
    output_type=list[MessagePart],
    model_settings=ModelSettings(temperature=0, tool_choice="required"),
)
