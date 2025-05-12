import json
import re
from dataclasses import dataclass
from datetime import datetime

import pytz
from app.configs import env_config
from app.configs.database import async_session, with_session
from app.repositories import sheet_repository
from app.services.integrations import sheet_rag_service
from app.utils.agent_utils import is_read_only_sql
from fuzzywuzzy import process
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from sqlalchemy import text


@dataclass
class SheetAgentDeps:
    user_input: str
    user_id: str
    script_context: str
    # context_memory: str
    timezone: str = "Asia/Ho_Chi_Minh"


instructions = """
From the user's message and provided context, construct sql and use tool to query more information with sheet data.
Carefully study the user's message, the context of scripts, sheet columns to provide more information about the customer's needs.
Strictly follow the descriptions of the tools.
From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description, example data. 
After analyzing the sheets, you can write sql query and use the `execute_query_on_sheet_rows` tool to query the sheet data. Do not return sql query in final response.
After querying, you must re examine the data if suitable for the user's needs. If not you can perform more queries.
You are also provided with the RAG tool to query vector database, each vector contains an entire row of sheet.
If query SQL not return appropriate data, you can fall back to RAG tool, but notice that results from RAG are just relevant data and not the accurate data.
You need to verify the data from RAG before returning to the user.
If you don't find any data after utilizing both tools, you can return a message that no data found. DO NOT return any information if don't use any tools.
"""
model = OpenAIModel(
    "deepseek-chat",
    provider=OpenAIProvider(
        base_url="https://api.deepseek.com", api_key=env_config.DEEPSEEK_API_KEY
    ),
)
sheet_agent = Agent(
    model=model,
    instructions=instructions,
    retries=3,
    output_type=str,
    output_retries=3,
    model_settings=ModelSettings(temperature=0, timeout=120),
)


@sheet_agent.instructions
async def get_current_local_time(context: RunContext[SheetAgentDeps]) -> str:
    """
    Get the current local time.
    """
    tz = pytz.timezone(context.deps.timezone)
    local_time = datetime.now(tz)
    return f"Current local time at {context.deps.timezone} is: {str(local_time)}\n"


# @sheet_agent.instructions
# async def get_context_memory(
#     context: RunContext[SheetAgentDeps],
# ) -> str:
#     """
#     Get context memory from the database.
#     """
#     context = context.deps.context_memory
#     return f"\nRelevant information from previous conversations:\n{context}"


@sheet_agent.instructions
async def get_scripts_context(
    context: RunContext[SheetAgentDeps],
) -> str:
    """
    Get all associated scripts from the database.
    """
    script_context = context.deps.script_context
    return f"\nRelevant information from scripts:\n{script_context}"


@sheet_agent.instructions
async def get_all_available_sheets(
    context: RunContext[SheetAgentDeps],
) -> str:
    """
    Get associated sheet from the database.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
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
        # for i, sheet in enumerate(sheets):
        #     example = await with_session(
        #         lambda session: sheet_repository.get_example_rows_by_sheet_id(
        #             session, sheet.id)
        #     )
        #     sheet_list[i]["example_rows"] = limit_sample_rows_content(example)
        return (
            f"\nHere is relevant sheet:\n{json.dumps(sheet_list, ensure_ascii=False)}"
        )
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


@sheet_agent.tool_plain(require_parameter_descriptions=True)
async def rag_hybrid_search(sheet_id: str, query: str, limit: int) -> list[str]:
    """
    Use this tool to query from the RAG (Retrieval-Augmented Generation) database.
    Your input query will be converted into both sparse and dense embeddings.
    - Sparse vector (BM25) captures exact keyword matches and term importance based on token frequency.
    It is effective for precise matches on specific terms or phrases.
    - Dense vector (text-embedding) captures semantic meaning and contextual similarity.
    It helps retrieve relevant results even when keywords are not exactly matched.
    The combined retrieval (dense + sparse fusion) balances precision and semantic relevance,
    providing high-quality context for downstream tasks like question answering or summarization.
    Results are returned as a list of text entries. Each entry represents a row from a knowledge sheet
    identified by 'sheet.id' in the 'sheet' table of database.

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


@sheet_agent.tool(retries=5)
async def execute_query_on_sheet_rows(
    context: RunContext[SheetAgentDeps], query: str
) -> list[dict[str, any]]:
    """
    Use this tool to query from {sheet.table_name} when you know the table_name via the sheet you are querying. FROM "{sheet.table_name}" is the table name you need to query from.
    You can use other fields of {table_name} specified in {sheet.column_config}, with normal operations to filter the query.
    You shoule use &@~ instead of LIKE, ILIKE against string, text field of "{sheet.table_name}" to perform fulltext search, examine 'sheet.column_config' field of that sheet in 'sheets' table to know about these columns.
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
    You must enclose the table name and column names in double quotes.
    Carefully try different keywords when using LIKE, ILIKE for fulltext search.
    Dont use single quotes for table name and column names.

    For example:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE "product_price" > 100

    How to use PGroonga for text fields
    &@~ operator
    You can use &@~ operator to perform full text search by query syntax such as keyword1 OR keyword2:

    SELECT * FROM memos WHERE content &@~ 'PGroonga OR PostgreSQL';
    --  id |                            content
    -- ----+----------------------------------------------------------------
    --   3 | PGroonga is a PostgreSQL extension that uses Groonga as index.
    --   1 | PostgreSQL is a relational database management system.
    -- (2 rows)
    Query syntax is similar to syntax of Web search engine ( keyword1 OR keyword2 means OR search and keyword1 keyword2 means AND search ). For example, you can use OR to merge result sets of performing full text search by two or more words. In the above example, you get a merged result set. The merged result set has records that includes PGroonga or PostgreSQL.
    You must always enclose the pgroonga query in parentheses, for example: FROM "some_table_name" WHERE ("data_fts" &@~ 'a OR b')​

    Example 1:
    If the input keyword string is: 'tàn nhang'
    Then the SQL query should be:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE ("description" &@~ 'tàn nhang')

    Normal query without fulltext search.
    Example 2:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name" as tb
    WHERE tb."product_price" > 100
    """
    try:
        async with async_session() as db:
            query = normalize_postgres_query(query)
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
            f"Error executing query: {str(e)}. Please check your query again."
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


def normalize_query_quotes(query: str) -> str:
    """
    Normalize SQL query by ensuring table names are properly quoted with double quotes.
    """
    # Replace any single quotes around table names with double quotes
    # FROM 'table_name' -> FROM "table_name"
    query = re.sub(r"FROM\s+'([^']+)'", r'FROM "\1"', query, flags=re.IGNORECASE)

    # Also ensure table names after FROM are in double quotes
    # FROM table_name -> FROM "table_name"
    query = re.sub(
        r"FROM\s+([a-zA-Z0-9_]+)(?!\s*\"|\s*\')",
        r'FROM "\1"',
        query,
        flags=re.IGNORECASE,
    )

    return query


def normalize_postgres_query(query: str) -> str:
    """
    Normalize Postgres SQL query for execution.
    - Ensure table names are properly quoted
    - Handle escaped quotes
    """
    # First normalize quotes for table names
    query = normalize_query_quotes(query)

    # Then handle escaped quotes
    query = re.sub(r"\\'", "'", query)

    return query
