"""
Các định nghĩa SQL cần thiết cho hệ thống
"""

# Setup PGroonga extension
SETUP_PGROONGA = """
CREATE EXTENSION IF NOT EXISTS pgroonga;
"""

# Index PGroonga cho full-text search trên các trường văn bản của guest_infos
CREATE_PGROONGA_GUEST_INFO_INDEX = """
CREATE INDEX IF NOT EXISTS pgroonga_guest_info_fullname_index ON guest_infos
USING pgroonga (fullname pgroonga_varchar_full_text_search_ops_v2);

CREATE INDEX IF NOT EXISTS pgroonga_guest_info_phone_index ON guest_infos
USING pgroonga (phone pgroonga_varchar_full_text_search_ops_v2);

CREATE INDEX IF NOT EXISTS pgroonga_guest_info_email_index ON guest_infos
USING pgroonga (email pgroonga_varchar_full_text_search_ops_v2);

CREATE INDEX IF NOT EXISTS pgroonga_guest_info_address_index ON guest_infos
USING pgroonga (address pgroonga_text_full_text_search_ops_v2);
"""


async def create_custom_functions_and_triggers(conn):
    """
    Thiết lập PGroonga extension, xóa bỏ các triggers, functions, và indexes cũ không còn sử dụng,
    và tạo index PGroonga mới cho guest_infos.
    """
    try:
        # Setup PGroonga extension
        await conn.execute(SETUP_PGROONGA)

        # Tạo index PGroonga mới cho các trường cụ thể của guest_info
        await conn.execute(CREATE_PGROONGA_GUEST_INFO_INDEX)

        print("PGroonga setup successfully.")
    except Exception as e:
        print(f"Lỗi khi thực thi SQL setup: {e}")
        raise
