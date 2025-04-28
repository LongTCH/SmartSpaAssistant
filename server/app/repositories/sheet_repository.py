from app.models import Sheet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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


async def update_sheet(db: AsyncSession, sheet: Sheet) -> Sheet:
    """
    Update an existing sheet in the database.
    """
    db.add(sheet)
    return sheet


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
