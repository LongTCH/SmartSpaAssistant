import json
import re
from dataclasses import dataclass
from datetime import datetime

import logfire
import pytz
from app.configs.database import async_session, with_session
from app.repositories import sheet_repository
from app.utils.agent_utils import (
    is_read_only_sql,
    is_sql_query,
    limit_sample_rows_content,
)
from fuzzywuzzy import process
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from sqlalchemy import text

logfire.configure(send_to_logfire="if-token-present")
logger = logfire.instrument_pydantic_ai()


@dataclass
class SheetDeps:
    context_memory: str
    latest_message: str
    timezone: str = "Asia/Ho_Chi_Minh"


instructions = """
## Character
Your name is Nguyen Thi Phuong Thao, a customer service staff at a spa specializing in skin care called Mailisa.
You are female, 25 years old, dynamic, polite, supportive, well-explain and soft-spoken.
Never send a message like "I will look up information and advise you in detail. Just a little time!", don't make the customer wait, always look up data to reply.
Always response with lookup data, never response with fake data.
## Skills
### Skill 1: Know to use tools effectively.
- Think: Use this tool before answering any detail information. 
- Strictly follow the descriptions of the tools.
- From published sheets available from database, you need to analyze the sheets including their names, descriptions, schema, and example data. This is helpful for you to make appropriate type conversions for each property in the query.
- After analyzing the sheets, you can write sql query and use execute_query_on_sheet_rows tool to query from 'sheet_rows' table with appropriate sheet id. Do not return sql query in final response.

### Skill 2: Take time to think carefully about the answer to give the most accurate one.
- If you can't get any information, rethink from start for 2-3 times because you could be wrong at some before steps. After that, if you still don't know, frankly say you don't know and ask the customer to contact the HOTLINE number or go directly to Mailisa's facilities for direct support.

### Skill 3: Provide more and more useful information that you knows than just the customer's question in order to convince them to buy products or use services. But keep short, concise, do not mess customers with mass of data. Determine which information is necessary. You can send media file to customer by link.
"""

sheet_agent = Agent(
    model="google-gla:gemini-2.0-flash",
    instructions=instructions,
    retries=2,
    output_type=str,
    output_retries=3,
)


# @sheet_agent.output_validator
# async def validate_sheet_output(
#     context: RunContext[None], output: str
# ) -> str:
#     """
#     Validate the output of the sheet agent.
#     """
#     if not isinstance(output, str):
#         raise ModelRetry("Invalid output format. Expected a string.")
#     response: AgentRunResult = await check_wait_resp_agent.run(user_prompt=output)
#     if "True" in response.output:
#         raise ModelRetry(
#             "Response indicates that the user should wait. Please retry to avoid making the user wait."
#         )
#     return output


@sheet_agent.instructions
async def get_current_local_time(context: RunContext[SheetDeps]) -> str:
    """
    Get the current local time.
    """
    tz = pytz.timezone(context.deps.timezone)
    local_time = datetime.now(tz)
    return f"Current local time at {context.deps.timezone} is: {str(local_time)}\n"


@sheet_agent.instructions
async def get_context_memory(
    context: RunContext[SheetDeps],
) -> str:
    """
    Get context memory from the database.
    """
    if not context.deps.context_memory:
        return ""
    return f"Relevant information from previous conversations:\n{context.deps.context_memory}"


@sheet_agent.instructions
async def get_all_published_sheets(
    context: RunContext[SheetDeps],
) -> str:
    """
    Get all published sheets from the database.
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
                "sample_rows": limit_sample_rows_content(sheet.sample_rows),
            }
            for sheet in sheets
        ]
        return f"""
        Here are all the published sheets: {json.dumps(sheet_list, ensure_ascii=False)}
        """
    except Exception as e:
        print(f"Error fetching sheets: {e}")
        return f"Error fetching sheets: {str(e)}"


@sheet_agent.tool(retries=3)
async def execute_query_on_sheet_rows(
    context: RunContext[None], query: str
) -> list[dict[str, any]]:
    """
        Use this tool to query from 'sheet_rows' table when you know the ID of the sheet you are querying. The ID of the sheet is the 'sheet_id', always add 'sheet_id' in query as FROM sheet_rows WHERE sheet_id = ? AND data &@~ ?.
    You always use the 'data' field of 'sheet_rows' to select, filter..., this is a jsonb type field containing all the keys read from the 'schema' field of that sheet in 'sheets' table.
    Always use Process keywords tool before this tool if you want to filter by keywords.
    Always use keys from 'schema' of sheet to append after 'data->' of 'sheet_rows' table to query.
    Always name the output column for the query.
    For example: data->'first_property' AS first_property, data->'second_property' AS second_property, because 'schema' in sheet contains 'first_property', 'second_property'.
    NOTICE: The table to query FROM is 'sheet_rows'

    Use Pgroonga specific operators to filter on 'data' field. Below is introduction.
    How to use PGroonga for JSON
    PGroonga also supports jsonb type. You can search JSON data by one or more keys and/or one or more values with PGroonga.

    You can also search JSON data by full text search against all text values in JSON. It's an unique feature of PGroonga.

    Think about the following JSON:

    {
      "message": "Server is started.",
      "host": "www.example.com",
      "tags": [
        "web"
      ]
    }
    You can find the JSON by full text search with server, example, or web because all text values are full text search target.

    &@~ operator is a PGroonga original operator. You can perform full text search against all texts in JSON by query syntax.

    Sample schema and data
    Here are sample schema and data for examples:

    CREATE TABLE logs (
      record jsonb
    );

    CREATE INDEX pgroonga_logs_index ON logs USING pgroonga (record);

    INSERT INTO logs
         VALUES ('{
                    "message": "Server is started.",
                    "host":    "www.example.com",
                    "tags": [
                      "web",
                      "example.com"
                    ]
                  }');
    INSERT INTO logs
         VALUES ('{
                    "message": "GET /",
                    "host":    "www.example.com",
                    "code":    200,
                    "tags": [
                      "web",
                      "example.com"
                    ]
                  }');
    INSERT INTO logs
         VALUES ('{
                    "message": "Send to <info@example.com>.",
                    "host":    "mail.example.net",
                    "tags": [
                      "mail",
                      "example.net"
                    ]
                  }');


    &@~ operator
    &@~ operator is a PGroonga original operator. You can perform full text search against all texts in JSON by query syntax.

    Here is an example to search "server" or "send" in JSON:

    SELECT jsonb_pretty(record) FROM logs WHERE record &@~ 'server OR send';
    --                  jsonb_pretty
    -- ----------------------------------------------
    --  {                                           +
    --      "host": "www.example.com",              +
    --      "tags": [                               +
    --          "web",                              +
    --          "example.com"                       +
    --      ],                                      +
    --      "message": "Server is started."         +
    --  }
    --  {                                           +
    --      "host": "mail.example.net",             +
    --      "tags": [                               +
    --          "mail",                             +
    --          "example.net"                       +
    --      ],                                      +
    --      "message": "Send to <info@example.com>."+
    --  }
    -- (2 rows)

    You must always enclose the pgroonga query in parentheses, for example: WHERE sheet_id = '213123423hidsaf' AND (data &@~ 'a OR b')​

    Example:
    If the input keyword string is: 'tàn nhang'
    Then the SQL query should be:
    SELECT
      data->'product_name' AS product_name,
      data->'discounted_price' AS discounted_price
    FROM sheet_rows
    WHERE sheet_id = 'some_sheet_id'
    AND (data &@~ 'tàn nhang')

    If you want to compare text, use data->> instead of data->.
    For example:
    SELECT
      data->'product_name' AS product_name,
      data->'discounted_price' AS discounted_price
    FROM sheet_rows
    WHERE sheet_id = 'some_sheet_id'
    AND (data->>'product_name' = 'tàn nhang')
    """
    try:
        async with async_session() as db:
            query = normalize_postgres_query(query)
            # Kiểm tra có tồn tại từ khóa sheet_id trong query không
            match = re.search(r"sheet_id\s*=\s*'([^']+)'", query)
            if not match:
                raise ModelRetry("Query must contains constraint with 'sheet_id'.")
            if not is_sql_query(query):
                raise ModelRetry(
                    "Query must be a valid SQL query. Please check your query again."
                )
            if not is_read_only_sql(query):
                raise ModelRetry(
                    "Query must be read-only SQL. Please check your query again."
                )
            # Lấy danh sách sheet_id từ cơ sở dữ liệu
            published_sheets = await sheet_repository.get_all_sheets_by_status(
                db, "published"
            )
            available_sheet_ids = [sheet.id for sheet in published_sheets]
            query = replace_sheet_id_if_needed(query, available_sheet_ids)
            # execute the query and return the result
            result = await db.execute(text(query))
            # Fetch all results as dictionaries
            rows = result.mappings().all()
            # Convert SQLAlchemy result to list of dictionaries
            return [dict(row) for row in rows]
    except ModelRetry as model_retry:
        raise model_retry
    except Exception as e:
        print(f"Error executing query: {e}")
        raise ModelRetry(
            f"Error executing query: {str(e)}. Please check your query again."
        )


def get_sheet_id_from_query(query: str) -> str:
    """
    Trích xuất sheet_id từ câu truy vấn SQL.
    """
    match = re.search(r"sheet_id\s*=\s*'([^']+)'", query)
    if match:
        return match.group(1)
    raise ModelRetry("Không tìm thấy sheet_id trong câu truy vấn.")


def replace_sheet_id_if_needed(query: str, available_sheet_ids: list[str]) -> str:
    # Bước 1: Trích xuất sheet_id từ query
    sheet_id_in_query = get_sheet_id_from_query(query)

    # Bước 2: Kiểm tra xem sheet_id có nằm trong danh sách không
    if sheet_id_in_query in available_sheet_ids:
        return query  # Không cần thay thế

    # Bước 3: Tìm sheet_id tương đồng nhất
    best_match, score = process.extractOne(sheet_id_in_query, available_sheet_ids)

    # Tuỳ chọn: nếu điểm tương đồng thấp quá, có thể không thay
    if score < 60:
        raise ModelRetry(
            f"Invalid sheet_id: {sheet_id_in_query}. Need to try with existing sheet_id."
        )

    # Bước 4: Thay sheet_id bằng best_match dùng hàm thay thế an toàn (lambda để tránh lỗi group reference)
    new_query = re.sub(
        r"(sheet_id\s*=\s*')[^']+(')",
        lambda m: m.group(1) + best_match + m.group(2),
        query,
    )
    return new_query


def normalize_postgres_query(query: str) -> str:
    # Thay thế \' bằng ' nhưng chỉ khi nó được escape không cần thiết
    # (tức là không phải dấu nháy đơn trong chuỗi SQL string literal)

    # Cách làm an toàn: chỉ thay thế \'
    # 1. Tìm các đoạn có dạng ->>\'...\' hoặc các chuỗi \'...\'
    return re.sub(r"\\'", "'", query)
