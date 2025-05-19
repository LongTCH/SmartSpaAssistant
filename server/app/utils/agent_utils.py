import hashlib
import json
import re
from typing import Any, Literal

import sqlparse
from pydantic import BaseModel, Field, TypeAdapter
from unidecode import unidecode


class MessagePart(BaseModel):
    type: Literal["text", "image", "video", "audio", "file", "link"] = Field(
        description="""
        The type of the message part. Possible values are:
        'text': Plain text message.
        'image': URL pointing to an image.
        'video': URL pointing to a video.
        'audio': URL pointing to an audio file.
        'file': URL pointing to a file.
        'link': URL to a web resource. A preceding 'text' message content must describe the link
        """,
    )
    payload: str = Field(
        description="""
        The content is a string if the type is "text".
        The content is a URL if the type is "image", "video", "audio", or "file".
        """,
    )


def is_read_only_sql(sql_text: str) -> bool:
    """
    Trả về True nếu sql_text chỉ chứa các câu lệnh read-only:
    - DQL: SELECT, WITH
    - Metadata: SHOW, DESCRIBE, EXPLAIN
    Ngược lại trả về False (INSERT, UPDATE, DELETE, DDL, hoặc không phải SQL).
    """
    # 1. Loại bỏ comment và whitespace dư thừa
    cleaned = sqlparse.format(sql_text, strip_comments=True).strip()
    if not cleaned:
        return False

    # 2. Dùng regex để kiểm tra từ khóa đầu (case-insensitive)
    pattern = r"(?i)^(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN)\b"
    if not re.match(pattern, cleaned):
        return False

    # Nếu khớp regex đầu, coi là read-only SQL
    return True


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


def limit_text_words(text, max_characters=500):
    """Limit text to a maximum number of characters and add '...' if truncated.
    Returns the original text if it's shorter than max_characters.
    """
    if not text or not isinstance(text, str):
        return text

    if len(text) <= max_characters:
        return text

    # Chỉ cắt đến số ký tự tối đa và thêm dấu "..."
    return text[:max_characters].rstrip() + "..."


def limit_sample_rows_content(sample_rows, max_characters=500):
    """Limit the length of text fields in sample_rows JSON content."""
    if not sample_rows:
        return sample_rows

    if isinstance(sample_rows, str):
        try:
            data = json.loads(sample_rows)
        except json.JSONDecodeError:
            # If it's not valid JSON, just limit the whole string
            return limit_text_words(sample_rows, max_characters)
    else:
        data = sample_rows

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = limit_text_words(value, max_characters)
            elif isinstance(value, (dict, list)):
                data[key] = limit_sample_rows_content(value, max_characters)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = limit_sample_rows_content(item, max_characters)

    return data


def dump_json(data: Any, *, indent: int = None, exclude_none: bool = False) -> str:
    """
    Tuần tự hóa dữ liệu thành chuỗi JSON, hỗ trợ các kiểu dữ liệu phức tạp.

    :param data: Dữ liệu cần tuần tự hóa (có thể là mô hình Pydantic, danh sách, từ điển, v.v.).
    :param indent: Số khoảng trắng để thụt lề trong chuỗi JSON (mặc định là None).
    :param exclude_none: Loại bỏ các trường có giá trị None nếu đặt là True.
    :return: Chuỗi JSON đại diện cho dữ liệu.
    """
    adapter = TypeAdapter(type(data))
    return adapter.dump_json(data, indent=indent, exclude_none=exclude_none).decode(
        "utf-8"
    )


def normalize_tool_name(text: str) -> str:
    # Dùng unidecode để phiên âm tất cả ký tự Unicode sang Latin
    transliterated = unidecode(text)

    # Chuyển sang chữ thường và thay thế ký tự không hợp lệ bằng dấu -
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", transliterated).strip("_-").lower()

    # Nếu kết quả quá ngắn, dùng mã băm
    if not normalized or len(normalized) < 3:
        normalized = "tool_" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]

    # Nếu bắt đầu bằng số, thêm dấu gạch dưới
    if normalized[0].isdigit():
        normalized = "_" + normalized

    return normalized[:64]


class CurrentTimeResponse(BaseModel):
    timezone: str = Field(
        description="The timezone in which the current time is provided."
    )
    current_time: str = Field(
        description="The current time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS±HH:MM)."
    )
