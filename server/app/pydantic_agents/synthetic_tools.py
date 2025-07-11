import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pytz
from app.configs.constants import PARAM_VALIDATION
from app.configs.database import async_session, with_session
from app.repositories import notification_repository, sheet_repository
from app.services import alert_service, sheet_service
from app.services.integrations import sheet_rag_service
from app.utils import string_utils
from app.utils.agent_utils import (
    dump_json,
    is_read_only_sql,
    normalize_postgres_query,
    normalize_tool_name,
)
from pydantic_ai import RunContext, Tool
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.tools import ToolDefinition
from sqlalchemy import text
from thefuzz import process


@dataclass
class SyntheticAgentDeps:
    user_input: str
    user_id: str
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


def get_description_from_param(
    param_type: str, description: str, validation: str
) -> str:
    result = description
    if param_type == "DateTime":
        result = result + " **FORMAT: YYYY-MM-DD HH:MM:SS**"
    if validation == PARAM_VALIDATION.PHONE.value:
        result = (
            result
            + f" **VALIDATION: {validation} - Vietnam phone number format: +84xxxxxxxxx (10-11 digits after +84) or 0xxxxxxxxx (10-11 digits starting with 0). Examples: +84912345678, +84901234567, 0912345678, 0901234567**"
        )
    elif validation == PARAM_VALIDATION.EMAIL.value:
        result = (
            result
            + f" **VALIDATION: {validation} - Valid email format: username@domain.extension. Must contain @ symbol and valid domain. Examples: user@example.com, test.email@domain.vn**"
        )
    elif validation == PARAM_VALIDATION.ADDRESS.value:
        result = (
            result
            + f" **VALIDATION: {validation} - Complete address format: Street number + Street name, Ward/Commune, District, City/Province, Country (if international). Must include specific location details. Examples: 123 Nguyen Trai Street, Ben Thanh Ward, District 1, Ho Chi Minh City**"
        )
    return result


def create_tool(notification_id: str, guest_id: str, tool_info: Dict[str, Any]) -> Tool:
    async def tool_function(**kwargs) -> str:
        # Remove tool_description from kwargs if present
        kwargs.pop("tool_description", "")

        empty_params = []
        # loop all params in kwargs to check find all empty params
        for param_name in tool_info["parameters"]["properties"]:
            if param_name != "tool_description" and param_name not in kwargs:
                empty_params.append(param_name)
        if empty_params:
            raise ModelRetry(
                f"Missing required parameters, can't not send notification now: {', '.join(empty_params)}"
            )  # Validate parameters based on notification params configuration
        async with async_session() as session:
            notification = await notification_repository.get_notification_by_id(
                session, notification_id
            )

            # Collect all validation errors
            validation_errors = []
            if notification.params:
                for param_config in notification.params:
                    param_name = param_config.get("param_name")
                    param_type = param_config.get("param_type", "String")
                    validation = param_config.get("validation", "")

                    if param_name in kwargs:
                        param_value = str(kwargs[param_name])
                        error_message = validate_param_value(
                            param_name, param_value, param_type, validation
                        )
                        if error_message:  # If there's a validation error
                            validation_errors.append(error_message)

            # If there are validation errors, raise ModelRetry with all errors
            if validation_errors:
                all_errors = "\n".join([f"- {error}" for error in validation_errors])
                raise ModelRetry(
                    f"Parameter validation failed. Please fix the following errors:\n{all_errors}"
                )

            template_str = notification.content
            alert_content = string_utils.render_tool_template(template_str, **kwargs)
            await alert_service.insert_custom_alert(
                session, guest_id, notification_id, alert_content
            )
            return f"""<status>success</status>
  <message>Alert '{notification.label}' has been sent with content:

{alert_content}
  </message>"""

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
        max_retries=2,
    )
    return tool


async def get_current_local_time(
    context: RunContext[SyntheticAgentDeps],
) -> str:
    """
    Get datetime (ISO Format) at local timezone in XML format.
    Use this when need to know the current time in the local timezone.
    """
    tz = pytz.timezone(context.deps.timezone)
    local_time = datetime.now(tz)

    # Return XML formatted string instead of object
    return f"""<timezone>{context.deps.timezone}</timezone>
    <time>{local_time.isoformat()}</time>"""


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
            "description": f"**Call this tool to notify admin when the following conditions are met:**\n{notification.description}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
        for param in notification.params:
            tool_json["parameters"]["properties"][param["param_name"]] = {
                "type": get_type_from_param_type(param["param_type"]),
                "description": get_description_from_param(
                    param["param_type"],
                    param["description"],
                    param.get("validation", ""),
                ),
            }
            tool_json["parameters"]["required"].append(param["param_name"])
        tool_json["parameters"]["properties"]["tool_description"] = {
            "type": "string",
            "description": "Tell me the details about the tool you are using.",
        }
        tool_json["parameters"]["required"].append("tool_description")
        notify_tools_json.append(tool_json)
    notify_tools = [
        create_tool(tool_info["notification_id"], guest_id, tool_info)
        for tool_info in notify_tools_json
    ]
    return notify_tools


async def rag_hybrid_search(sheet_id: str, query: str, limit: int) -> str:
    """
    Only use this tool if cannot find the data from SQL query.
    It is effective for precise matches on specific terms or phrases.

    Results are returned as a list of text entries. Each entry represents a row from a knowledge sheet
    identified by 'sheet.id' in the 'sheet' table of database.

    Args:
        sheet_id: The ID of the sheet to query.
        query: The query string to search for.
        limit: The maximum number of results to return. Must be enough large number to search relative data.
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
    return dump_json([sheet_chunk.chunk for sheet_chunk in sheet_chunks])


def rows_to_xml(rows: list[dict[str, Any]]) -> str:
    """
    Converts a list of dictionaries (rows) into an XML string.
    Each dictionary is converted to a <row> element,
    and its key-value pairs become child elements.
    """
    xml_parts = []
    for row_data in rows:
        row_element = ET.Element("row")
        for key, value in row_data.items():
            # Ensure element names are valid XML names (e.g., no spaces, not starting with numbers if not careful)
            # For simplicity, assuming keys are valid or need sanitization if not.
            # A basic sanitization could be to replace invalid characters or prefix numbers.
            # For now, we'll assume keys are simple enough.
            col_element = ET.SubElement(row_element, str(key))
            col_element.text = str(value)  # Ensure value is a string
        xml_parts.append(ET.tostring(row_element, encoding="unicode"))
    return "\n".join(xml_parts)


async def get_all_available_sheets(context: RunContext[SyntheticAgentDeps]) -> str:
    """
    Get all available sheets in XML Format from the database to analyze structure in order to construct sql query.
    """
    try:
        sheets = await with_session(
            lambda db: sheet_repository.get_all_sheets_by_status(db, "published")
        )
        if not sheets:
            return ""
        context = await sheet_service.agent_sheets_to_xml(sheets)

        return context
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


async def execute_query_on_sheet_rows(sql_query: str) -> str:
    """
    Carefully study the sheet_description before thinking about the SQL query.
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
    You must enclose the table name, column names, keywords in fulltext search in double quotes.
    Dont use single quotes for table name and column names.
    If using LIMIT must be enough large number to search relative data if not require a specific number.

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
                    "Using **rag_hybrid_search** tool to search by phrase for relevant items of sheet."
                )
            return rows_to_xml([dict(r) for r in rows])
    except ModelRetry as model_retry:
        raise model_retry
    except Exception as e:
        print(f"Error executing query: {e}")
        raise ModelRetry(
            f"Error executing query: {str(e)}. Please reanalyze sheets structure using **get_all_available_sheets** tool."
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


def validate_param_value(
    param_name: str, param_value: str, param_type: str, validation: str
) -> str:
    """
    Validate parameter value based on param_type and validation rules.
    Returns error message if validation fails, empty string if valid.

    Args:
        param_name: Name of the parameter
        param_value: Value to validate
        param_type: Type of the parameter (String, DateTime, etc.)
        validation: Validation rule (phone, email, address, etc.)

    Returns:
        str: Error message if validation fails, empty string if valid
    """
    # Check DateTime format
    if param_type == "DateTime":
        try:
            datetime.strptime(param_value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return (
                f"Invalid {param_name}: '{param_value}'. DateTime must be in format YYYY-MM-DD HH:MM:SS. "
                f"Example: 2024-12-25 14:30:00"
            )

    # Check validation rules
    if validation == PARAM_VALIDATION.PHONE.value:
        # Vietnam phone number validation - exactly matching the description format
        phone_pattern = r"^(\+84[0-9]{9,10}|0[0-9]{9,10})$"
        if not re.match(phone_pattern, param_value.replace(" ", "").replace("-", "")):
            return (
                f"Invalid {param_name}: '{param_value}'. Vietnam phone number format required: "
                f"+84xxxxxxxxx (10-11 digits after +84) or 0xxxxxxxxx (10-11 digits starting with 0). "
                f"Examples: +84912345678, +84901234567, 0912345678, 0901234567"
            )

    elif validation == PARAM_VALIDATION.EMAIL.value:
        # Email validation - exactly matching the description format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, param_value):
            return (
                f"Invalid {param_name}: '{param_value}'. Valid email format required: "
                f"username@domain.extension. Must contain @ symbol and valid domain. "
                f"Examples: user@example.com, test.email@domain.vn"
            )

    elif validation == PARAM_VALIDATION.ADDRESS.value:
        # Address validation - exactly matching the description format
        if len(param_value.strip()) < 10:
            return (
                f"Invalid {param_name}: '{param_value}'. Complete address format required: "
                f"Street number + Street name, Ward/Commune, District, City/Province, Country (if international). "
                f"Must include specific location details. "
                f"Examples: 123 Nguyen Trai Street, Ben Thanh Ward, District 1, Ho Chi Minh City"
            )

        # Check if address contains some basic components (comma separated parts)
        address_parts = [part.strip() for part in param_value.split(",")]
        if len(address_parts) < 3:
            return (
                f"Invalid {param_name}: '{param_value}'. Address must include at least 3 components separated by commas: "
                f"Street number + Street name, Ward/Commune, District, City/Province. "
                f"Examples: 123 Nguyen Trai Street, Ben Thanh Ward, District 1, Ho Chi Minh City"
            )

    return ""  # No validation errors
