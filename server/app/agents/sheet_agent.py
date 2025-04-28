import json
import re

from app.configs.database import async_session, with_session
from app.repositories import sheet_repository
from fuzzywuzzy import process
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from sqlalchemy import text

# @dataclass
# class SheetDeps:
#     db: AsyncSession = Field(description="Database session")


instructions = """
You are a helpful assistant that can help customers search for information with your sheets.
From published sheets available from database ,you need to analyze the sheets including their names, descriptions, schema, and example data.
After analyzing the sheets, you can write sql query and use execute_query_on_sheet_rows tool to query from 'sheet_rows' table with appropriate sheet id.
Do not return sql query in final response.
"""

sheet_agent = Agent(
    model="google-gla:gemini-2.0-flash",
    instructions=instructions,
    retries=2,
    output_type=str,
    output_retries=3,
)


@sheet_agent.instructions
async def get_all_published_sheets(
    context: RunContext[None],
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
        return f"Here are all the published sheets: {json.dumps(sheet_list, ensure_ascii=False)}"
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
    Always use keys from 'schema' of sheet to append after 'data->>' of 'sheet_rows' table to query.
    Always name the output column for the query.
    For example: data->>'first_property' AS first_property, data->>'second_property' AS second_property, because 'schema' in sheet contains 'first_property', 'second_property'.
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
      data->>'product_name' AS product_name,
      data->>'discounted_price' AS discounted_price
    FROM sheet_rows
    WHERE sheet_id = 'some_sheet_id'
    AND (data &@~ 'tàn nhang')
    """
    try:
        async with async_session() as db:
            query = normalize_postgres_query(query)
            # Kiểm tra có tồn tại từ khóa sheet_id trong query không
            match = re.search(r"sheet_id\s*=\s*'([^']+)'", query)
            if not match:
                raise ModelRetry("Query must contains constraint with 'sheet_id'.")
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
        return {"error": f"Query execution failed: {str(e)}"}


def limit_text_words(text, max_words=100):
    """Limit text to a maximum number of words and add '...' if truncated.
    Handles text with various separators commonly found in user editor content.
    """
    if not text or not isinstance(text, str):
        return text

    # Split text by multiple separators: spaces, newlines, tabs, commas, periods, etc.
    # This regex will treat any sequence of whitespace or common punctuation as a word separator
    words = re.split(r'[\s\t\n\r.,;:!?\(\)\[\]{}"\'\-_<>=/\\|]+', text)

    # Filter out empty strings that might result from the split
    words = [word for word in words if word.strip()]

    if len(words) <= max_words:
        return text

    # Rebuild the text with original formatting up to max_words
    # Find position where max_words ends
    count = 0
    position = 0

    for match in re.finditer(r"[\S]+", text):
        count += 1
        if count > max_words:
            position = match.start()
            break

    if position > 0:
        return text[:position].rstrip() + "..."
    else:
        # Fallback if regex approach doesn't work
        return " ".join(words[:max_words]) + "..."


def limit_sample_rows_content(sample_rows):
    """Limit the length of text fields in sample_rows JSON content."""
    if not sample_rows:
        return sample_rows

    if isinstance(sample_rows, str):
        try:
            data = json.loads(sample_rows)
        except json.JSONDecodeError:
            # If it's not valid JSON, just limit the whole string
            return limit_text_words(sample_rows)
    else:
        data = sample_rows

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = limit_text_words(value)
            elif isinstance(value, (dict, list)):
                data[key] = limit_sample_rows_content(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = limit_sample_rows_content(item)

    return data


def replace_sheet_id_if_needed(query: str, available_sheet_ids: list[str]) -> str:
    # Bước 1: Trích xuất sheet_id từ query
    match = re.search(r"sheet_id\s*=\s*'([^']+)'", query)
    if not match:
        raise ValueError("Không tìm thấy sheet_id trong query.")

    sheet_id_in_query = match.group(1)

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


def contains_sql_query(text: str) -> bool:
    # Các mẫu phổ biến của câu truy vấn SQL
    sql_patterns = [
        r"\bSELECT\b\s+.*?\bFROM\b",  # SELECT ... FROM ...
        r"\bINSERT\b\s+INTO\b",  # INSERT INTO ...
        r"\bUPDATE\b\s+\w+\s+\bSET\b",  # UPDATE ... SET ...
        r"\bDELETE\b\s+FROM\b",  # DELETE FROM ...
        r"\bCREATE\b\s+(TABLE|DATABASE)\b",  # CREATE TABLE / DATABASE
        r"\bDROP\b\s+(TABLE|DATABASE)\b",  # DROP TABLE / DATABASE
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True
    return False
