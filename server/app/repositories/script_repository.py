from app.models import Script, script_attachments
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


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
    stmt = (
        select(Script)
        .options(selectinload(Script.related_scripts))
        .where(Script.id == script_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_script(db: AsyncSession, script: Script) -> Script:
    db.add(script)
    await db.flush()
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


async def get_all_scripts(db: AsyncSession) -> list[Script]:
    """
    Get all scripts from the database.
    """
    stmt = (
        select(Script)
        .options(selectinload(Script.related_scripts))
        .order_by(Script.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_scripts_by_status(db: AsyncSession, status: str) -> list[Script]:
    """
    Get all scripts from the database.
    """
    stmt = (
        select(Script)
        .options(selectinload(Script.related_scripts))
        .where(Script.status == status)
        .order_by(Script.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def insert_scripts(db: AsyncSession, scripts: list[Script]) -> list[Script]:
    """
    Insert multiple scripts into the database.
    """
    db.add_all(scripts)
    await db.flush()
    return scripts


async def get_related_scripts(db: AsyncSession, script_id: str) -> list[Script]:
    """
    Get all scripts related to a given script.
    """
    stmt = (
        select(Script)
        .options(selectinload(Script.related_scripts))
        .where(Script.id == script_id)
    )
    result = await db.execute(stmt)
    script = result.scalars().first()

    if script and hasattr(script, "related_scripts"):
        return script.related_scripts
    return []


async def get_attached_to_scripts(db: AsyncSession, script_id: str) -> list[Script]:
    """
    Get all scripts that a given script is attached to.
    This retrieves scripts where the given script appears as a related script.
    """
    stmt = (
        select(Script)
        .options(selectinload(Script.attached_scripts))
        .where(Script.id == script_id)
    )
    result = await db.execute(stmt)
    script = result.scalars().first()

    if script and hasattr(script, "attached_scripts"):
        return script.attached_scripts
    return []


async def get_scripts_by_ids(db: AsyncSession, script_ids: list[str]) -> list[Script]:
    """
    Get scripts by their IDs.
    """
    stmt = (
        select(Script)
        .options(selectinload(Script.related_scripts))
        .where(Script.id.in_(script_ids))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def insert_related_scripts(
    db: AsyncSession, script_id: str, related_script_ids: list[str]
) -> None:
    """
    Insert related scripts for a given script.
    """
    for related_id in related_script_ids:
        stmt = insert(script_attachments).values(
            parent_script_id=script_id, attached_script_id=related_id
        )
        await db.execute(stmt)


async def delete_related_scripts(
    db: AsyncSession, script_id: str, related_script_ids: list[str]
) -> None:
    """
    Delete related scripts for a given script.
    """
    stmt = delete(script_attachments).where(
        script_attachments.c.parent_script_id == script_id,
        script_attachments.c.attached_script_id.in_(related_script_ids),
    )
    await db.execute(stmt)
