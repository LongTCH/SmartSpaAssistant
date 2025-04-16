from app.models import SheetRow
from sqlalchemy.ext.asyncio import AsyncSession


def insert_or_update(db: AsyncSession, sheet_rows: list[SheetRow]) -> None:
    db.add_all(sheet_rows)
