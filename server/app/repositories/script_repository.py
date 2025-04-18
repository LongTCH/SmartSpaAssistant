from app.models import Script
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def count_scripts(db: AsyncSession) -> int:
    stmt = select(Script)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_scripts_by_status(db: AsyncSession, status: str) -> int:
    stmt = select(Script).where(Script.status == status)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_scripts(db: AsyncSession, skip: int, limit: int) -> list[Script]:
    stmt = select(Script).order_by(Script.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_scripts_by_status(
    db: AsyncSession, skip: int, limit: int, status: str
) -> list[Script]:
    stmt = select(Script).where(Script.status == status).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_script_by_id(db: AsyncSession, script_id: str) -> Script:
    stmt = select(Script).where(Script.id == script_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_script(db: AsyncSession, script: Script) -> Script:
    db.add(script)
    return script


async def update_script(db: AsyncSession, script: Script) -> Script:
    db.add(script)
    return script


async def delete_script(db: AsyncSession, script_id: str) -> None:
    stmt = select(Script).where(Script.id == script_id)
    result = await db.execute(stmt)
    script = result.scalars().first()
    if script:
        await db.delete(script)
    return None


async def delete_multiple_scripts(db: AsyncSession, script_ids: list[str]) -> None:
    stmt = select(Script).where(Script.id.in_(script_ids))
    result = await db.execute(stmt)
    scripts = result.scalars().all()
    for script in scripts:
        await db.delete(script)
    return None
