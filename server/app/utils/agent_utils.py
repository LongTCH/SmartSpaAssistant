import json
import re

import sqlparse


def is_sql_query(text: str) -> bool:
    """
    Kiểm tra xem text có phải là một câu lệnh SQL hợp lệ cơ bản hay không.
    Trả về True nếu text chứa ít nhất một câu lệnh SQL (SELECT, INSERT, UPDATE, DELETE, ...).
    """
    if not isinstance(text, str):
        return False

    # 1. Loại bỏ comment và whitespace đầu/cuối
    cleaned = sqlparse.format(text, strip_comments=True).strip()
    if not cleaned:
        return False

    # 2. Dùng regex đơn giản kiểm tra từ khóa đầu (case-insensitive)
    #    Chỉ quan tâm token đầu, không dùng get_type() vì có thể trả về UNKNOWN với SQL phức tạp
    pattern = r"(?i)^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b"
    if not re.match(pattern, cleaned):
        return False

    # 3. Thử parse với sqlparse để chắc chắn không hoàn toàn vô nghĩa
    try:
        stmts = sqlparse.parse(cleaned)
    except Exception:
        return False
    if not stmts:
        return False

    return True


def is_read_only_sql(sql_text: str) -> bool:
    """
    Trả về True nếu sql_text chỉ chứa các câu lệnh read-only:
    - DQL: SELECT, WITH
    - Metadata: SHOW, DESCRIBE, EXPLAIN
    Ngược lại trả về False (INSERT, UPDATE, DELETE, DDL, hoặc không phải SQL).
    """
    if not isinstance(sql_text, str):
        return False

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
