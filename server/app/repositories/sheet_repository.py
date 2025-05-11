import json

from app.models import Sheet, script_sheets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import text


async def count_sheets(db: AsyncSession) -> int:
    """
    Count the total number of sheets in the database.
    """
    stmt = select(Sheet)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_sheets(db: AsyncSession, skip: int, limit: int) -> list[Sheet]:
    """
    Get a paginated list of sheets from the database.
    """
    stmt = select(Sheet).order_by(Sheet.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def count_sheets_by_status(db: AsyncSession, status: str) -> int:
    """
    Count the number of sheets in the database by status.
    """
    stmt = select(Sheet).where(Sheet.status == status)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_sheets_by_status(
    db: AsyncSession, skip: int, limit: int, status: str
) -> list[Sheet]:
    """
    Get a paginated list of sheets from the database by status.
    """
    stmt = select(Sheet).where(Sheet.status == status).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_sheet_by_id(db: AsyncSession, sheet_id: str) -> Sheet:
    """
    Get a sheet by its ID from the database.
    """
    stmt = select(Sheet).where(Sheet.id == sheet_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_sheet(db: AsyncSession, sheet: Sheet) -> Sheet:
    """
    Insert a new sheet into the database.
    """
    db.add(sheet)
    await db.flush()
    return sheet


async def update_sheet(db: AsyncSession, sheet_id: str, update_data: dict) -> Sheet:
    """
    Update specific fields of an existing sheet in the database.
    Only name, description, status, and column descriptions in column_config can be updated.

    Args:
        db: Database session
        sheet_id: ID of the sheet to update
        update_data: Dictionary containing fields to update

    Returns:
        Updated Sheet object
    """
    # Get the existing sheet
    existing_sheet = await get_sheet_by_id(db, sheet_id)
    if not existing_sheet:
        return None

    # Update allowed fields if they exist in the update_data
    if "name" in update_data:
        existing_sheet.name = update_data["name"]

    if "description" in update_data:
        existing_sheet.description = update_data["description"]

    if "status" in update_data and update_data["status"] in ["published", "draft"]:
        existing_sheet.status = update_data["status"]

    # Update column descriptions in column_config if provided
    if "column_config" in update_data:
        # Directly assign the column_config (it should already be a list or dict)
        existing_sheet.column_config = update_data["column_config"]

        # Đánh dấu cụ thể thuộc tính này đã thay đổi để SQLAlchemy cập nhật
        flag_modified(existing_sheet, "column_config")

    # Add the sheet to the session to mark it for update
    db.add(existing_sheet)

    return existing_sheet


async def delete_sheet(db: AsyncSession, sheet_id: str) -> None:
    """
    Delete a sheet from the database by its ID.
    """
    stmt = select(Sheet).where(Sheet.id == sheet_id)
    result = await db.execute(stmt)
    sheet = result.scalars().first()
    if sheet:
        await db.delete(sheet)
    return None


async def delete_multiple_sheets(db: AsyncSession, sheet_ids: list[str]) -> None:
    """
    Delete multiple sheets from the database by their IDs.
    """
    stmt = select(Sheet).where(Sheet.id.in_(sheet_ids))
    result = await db.execute(stmt)
    sheets = result.scalars().all()
    for sheet in sheets:
        await db.delete(sheet)
    return None


async def get_all_sheets_by_status(db: AsyncSession, status: str) -> list[Sheet]:
    """
    Get all sheets from the database.
    """
    stmt = select(Sheet).where(Sheet.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_sheets_by_ids(db: AsyncSession, sheet_ids: list[str]) -> list[Sheet]:
    """
    Get multiple sheets by their IDs from the database.
    """
    stmt = select(Sheet).where(Sheet.id.in_(sheet_ids))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_example_rows_by_sheet_id(db: AsyncSession, sheet_id: str) -> list[dict]:
    """
    Get the first two rows of a sheet by its table name from the database.
    """
    sheet = await get_sheet_by_id(db, sheet_id)
    if not sheet:
        return None
    table_name = sheet.table_name
    stmt = text(f'SELECT data_fts::text FROM "{table_name}" LIMIT 2')
    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [json.loads(row["data_fts"]) for row in rows]


async def get_sheet_ids_by_script_ids(
    db: AsyncSession, script_ids: list[str]
) -> list[str]:
    """
    Get the sheet IDs by script IDs from the database.
    """
    stmt = select(script_sheets).where(script_sheets.c.script_id.in_(script_ids))
    result = await db.execute(stmt)
    return [row[1] for row in result.fetchall()]


async def get_all_rows_with_sheet_and_columns(
    db: AsyncSession, table_name: str, columns: list[str]
) -> list[dict]:
    selected_columns = ", ".join([f'"{col}"' for col in columns])
    query = text(f'SELECT {selected_columns} FROM "{table_name}" ORDER BY id')
    result = await db.execute(query)
    return result.mappings().all()


async def count_rows_of_sheet(db: AsyncSession, table_name: str) -> int:
    query = text(f'SELECT COUNT(*) FROM "{table_name}"')
    result = await db.execute(query)
    return result.scalar()


async def get_rows_with_columns(
    db: AsyncSession, table_name: str, columns: list[str], skip: int, limit: int
) -> list[dict]:
    selected_columns = ", ".join([f'"{col}"' for col in columns])
    query = text(
        f'SELECT {selected_columns} FROM "{table_name}" ORDER BY id LIMIT {limit} OFFSET {skip}'
    )
    result = await db.execute(query)
    return result.mappings().all()


async def get_all_rows_of_sheet(db: AsyncSession, table_name: str) -> list[dict]:
    query = text(f'SELECT * FROM "{table_name}" ORDER BY id')
    result = await db.execute(query)
    return result.mappings().all()
