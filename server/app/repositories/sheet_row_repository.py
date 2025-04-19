from app.models import SheetRow
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def insert_or_update(db: AsyncSession, sheet_rows: list[SheetRow]) -> None:
    db.add_all(sheet_rows)


async def get_all_sheet_rows_by_sheet_id(
    db: AsyncSession, sheet_id: str
) -> list[SheetRow]:
    """
    Get all rows of a sheet by its ID from the database.
    """
    stmt = (
        select(SheetRow).where(SheetRow.sheet_id == sheet_id).order_by(SheetRow.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_sheet_row_by__sheet_id(
    db: AsyncSession, sheet_id: str, skip: int, limit: int
) -> list[SheetRow]:
    """
    Get a paginated list of rows of a sheet by its ID from the database.
    """
    stmt = (
        select(SheetRow)
        .where(SheetRow.sheet_id == sheet_id)
        .order_by(SheetRow.order)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def count_sheet_rows_by_sheet_id(db: AsyncSession, sheet_id: str) -> int:
    """
    Count the number of rows of a sheet by its ID from the database.
    """
    stmt = select(SheetRow).where(SheetRow.sheet_id == sheet_id)
    result = await db.execute(stmt)
    return len(result.scalars().all())
