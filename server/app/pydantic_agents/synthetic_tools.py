import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Literal

import pytz
from app.configs.database import async_session, with_session
from app.repositories import (
    guest_info_repository,
    notification_repository,
    sheet_repository,
)
from app.services import alert_service, sheet_service
from app.services.integrations import sheet_rag_service
from app.utils import string_utils
from app.utils.agent_utils import (
    CurrentTimeResponse,
    is_read_only_sql,
    normalize_postgres_query,
    normalize_tool_name,
)
from fuzzywuzzy import process
from pydantic_ai import RunContext, Tool
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
        async with async_session() as session:
            notification = await notification_repository.get_notification_by_id(
                session, notification_id
            )
            template_str = notification.content
            alert_content = string_utils.render_tool_template(template_str, **kwargs)
            await alert_service.insert_custom_alert(
                session, guest_id, notification_id, alert_content
            )
            return {
                "status": "success",
                "message": f"Alert {notification.label} has been sent with content:\n\n{alert_content}",
            }

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


async def get_notify_tools(guest_id: str) -> list[Tool]:
    notify_tools_json = []
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
        notify_tools_json.append(tool_json)
    notify_tools = [
        create_tool(tool_info["notification_id"], guest_id, tool_info)
        for tool_info in notify_tools_json
    ]
    return notify_tools


async def rag_hybrid_search(sheet_id: str, query: str, limit: int) -> list[str]:
    """
    Only use this tool if cannot find the data from SQL query.
    Use this tool to query from the RAG (Retrieval-Augmented Generation) database.
    Sparse vector (BM25) captures exact keyword matches and term importance based on token frequency.
    It is effective for precise matches on specific terms or phrases.

    Results are returned as a list of text entries. Each entry represents a row from a knowledge sheet
    identified by 'sheet.id' in the 'sheet' table of database.
    Use this tool to search relative items when 'execute_query_on_sheet_rows' tool not returning appropriate data.

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

        return context
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


async def execute_query_on_sheet_rows(
    explain: str, sql_query: str
) -> list[dict[str, any]] | str:
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
                return (
                    "No data found. Please check your query again."
                    "Or consider using *rag_hybrid_search* tool to search for relevant data."
                )
            return [dict(row) for row in rows]
    except ModelRetry as model_retry:
        raise model_retry
    except Exception as e:
        print(f"Error executing query: {e}")
        raise ModelRetry(
            f"Error executing query: {str(e)}. Please reanalyze sheets structure using *get_all_available_sheets* tool."
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


async def update_guest_fullname(
    context: RunContext[SyntheticAgentDeps], fullname: str
) -> None:
    """
    Update the current guest's fullname in the database.

    Args:
        context: The run context containing dependencies.
        fullname: The new fullname to set for the guest.
    """
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            guest_info.fullname = fullname
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest fullname updated to {fullname}",
        }


async def update_guest_birthday(
    context: RunContext[SyntheticAgentDeps], birthday: str
) -> None:
    """
    Update the current guest's birthday in the database. If just the year is provided, set the birthday to the first day of that year.
    If the birthday is not in the correct format, raise an exception.

    Args:
        context: The run context containing dependencies.
        birthday: The new birthday to set for the guest, formatted as YYYY-MM-DD.
    """
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            date_time_obj = datetime.strptime(birthday, "%Y-%m-%d")
            guest_info.birthday = date_time_obj
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest birthday updated to {birthday}",
        }


async def update_guest_phone(
    context: RunContext[SyntheticAgentDeps], phone: str
) -> None:
    """
    Update the current guest's phone number in the database.

    Args:
        context: The run context containing dependencies.
        phone: The new phone number to set for the guest.
    """
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            guest_info.phone = phone
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest phone updated to {phone}",
        }


async def update_guest_email(
    context: RunContext[SyntheticAgentDeps], email: str
) -> None:
    """
    Update the current guest's email in the database.

    Args:
        context: The run context containing dependencies.
        email: The new email to set for the guest.
    """
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            guest_info.email = email
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest email updated to {email}",
        }


async def update_guest_address(
    context: RunContext[SyntheticAgentDeps], address: str
) -> None:
    """
    Update the current guest's address in the database.

    Args:
        context: The run context containing dependencies.
        address: The new address to set for the guest.
    """
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            guest_info.address = address
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest address updated to {address}",
        }


async def update_guest_gender(
    context: RunContext[SyntheticAgentDeps], gender: Literal["male", "female"]
) -> None:
    """
    Update the current guest's gender in the database.

    Args:
        context: The run context containing dependencies.
        gender: The new gender to set for the guest, must be either 'male' or 'female'.
    """
    if gender not in ["male", "female"]:
        raise ValueError("Invalid gender. Gender must be either 'male' or 'female'.")
    async with async_session() as session:
        try:
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, context.deps.user_id
            )
            guest_info.gender = gender
            await guest_info_repository.update_guest_info(session, guest_info)
            await session.commit()
        except Exception as e:
            await session.rollback()

        return {
            "status": "success",
            "message": f"Guest gender updated to {gender}",
        }
