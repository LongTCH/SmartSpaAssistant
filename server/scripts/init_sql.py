"""
Các định nghĩa SQL cần thiết cho hệ thống
"""

# Setup PGroonga extension
SETUP_PGROONGA = """
CREATE EXTENSION IF NOT EXISTS pgroonga;

CREATE INDEX IF NOT EXISTS pgroonga_sheet_row_data_index ON sheet_rows USING pgroonga (data);
"""

# Trigger để cập nhật trường data trong GuestInfo
UPDATE_GUEST_INFO_DATA_FUNCTION = """
CREATE OR REPLACE FUNCTION update_guest_info_data_function()
RETURNS TRIGGER AS $$
DECLARE
    interest_names TEXT[];
BEGIN
    -- Lấy danh sách tên interests
    SELECT ARRAY_AGG(i.name)
    INTO interest_names
    FROM interests i
    JOIN guest_interests gi ON i.id = gi.interest_id
    WHERE gi.guest_id = (SELECT id FROM guests WHERE info_id = NEW.id);
    
    -- Cập nhật trường data JSON, xử lý cẩn thận với null và array rỗng
    NEW.data = jsonb_build_object(
        'fullname', COALESCE(NEW.fullname, ''),
        'phone', COALESCE(NEW.phone, ''),
        'email', COALESCE(NEW.email, ''),
        'address', COALESCE(NEW.address, ''),
        'interests', CASE 
            WHEN interest_names IS NULL THEN '[]'::jsonb
            ELSE to_jsonb(interest_names)
        END
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

UPDATE_GUEST_INFO_DATA_TRIGGER = """
CREATE OR REPLACE TRIGGER update_guest_info_data_trigger
BEFORE INSERT OR UPDATE ON guest_infos
FOR EACH ROW
EXECUTE FUNCTION update_guest_info_data_function();
"""

# Trigger để cập nhật data khi thay đổi guest_interests
UPDATE_GUEST_INTEREST_DATA_FUNCTION = """
CREATE OR REPLACE FUNCTION update_guest_interest_data_function()
RETURNS TRIGGER AS $$
DECLARE
    guest_info_id TEXT;
BEGIN
    -- Lấy guest_info_id từ guest_id (xử lý cẩn thận với DELETE operation)
    IF TG_OP = 'DELETE' THEN
        SELECT info_id INTO guest_info_id FROM guests WHERE id = OLD.guest_id;
    ELSE
        SELECT info_id INTO guest_info_id FROM guests WHERE id = NEW.guest_id;
    END IF;
    
    -- Kích hoạt cập nhật guest_info bằng cách thực hiện UPDATE
    IF guest_info_id IS NOT NULL THEN
        UPDATE guest_infos SET updated_at = NOW() WHERE id = guest_info_id;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""

UPDATE_GUEST_INTEREST_TRIGGER = """
CREATE OR REPLACE TRIGGER update_guest_interest_trigger
AFTER INSERT OR UPDATE OR DELETE ON guest_interests
FOR EACH ROW
EXECUTE FUNCTION update_guest_interest_data_function();
"""

# Index PGroonga cho full-text search với tiếng Việt
CREATE_PGROONGA_INDEX = """
CREATE INDEX IF NOT EXISTS pgroonga_guest_info_data_index ON guest_infos
USING pgroonga (data)
WITH (
    tokenizer = 'TokenNgram("unigram_only", true, "loose_symbol", true)',
    normalizer = 'NormalizerNFKC100("unify_kana", false)'
);
"""

# Tạo một hàm để xóa các triggers nếu chúng đã tồn tại (để tránh lỗi khi redeploy)
DROP_EXISTING_TRIGGERS = """
DROP TRIGGER IF EXISTS update_guest_info_data_trigger ON guest_infos;
DROP TRIGGER IF EXISTS update_guest_interest_trigger ON guest_interests;
DROP FUNCTION IF EXISTS update_guest_info_data_function() CASCADE;
DROP FUNCTION IF EXISTS update_guest_interest_data_function() CASCADE;
"""

# Tạo một hàm để tạo các functions và triggers


async def create_custom_functions_and_triggers(conn):
    """
    Tạo các custom functions và triggers cần thiết trong database
    """
    try:
        # Setup PGroonga extension
        await conn.execute(SETUP_PGROONGA)

        # Xóa các triggers và functions hiện có
        await conn.execute(DROP_EXISTING_TRIGGERS)

        # Tạo các functions và triggers mới
        await conn.execute(UPDATE_GUEST_INFO_DATA_FUNCTION)
        await conn.execute(UPDATE_GUEST_INFO_DATA_TRIGGER)
        await conn.execute(UPDATE_GUEST_INTEREST_DATA_FUNCTION)
        await conn.execute(UPDATE_GUEST_INTEREST_TRIGGER)

        # Tạo index PGroonga cho guest_info
        await conn.execute(CREATE_PGROONGA_INDEX)

        print("Tất cả SQL functions và triggers đã được tạo thành công")
    except Exception as e:
        print(f"Lỗi khi tạo SQL functions và triggers: {e}")
        raise
