from app.dtos import PaginationDto
from app.models import Script
from app.repositories import script_repository
from sqlalchemy.ext.asyncio import AsyncSession


async def get_scripts(db: AsyncSession, page: int, limit: int) -> PaginationDto:
    """
    Get a paginated list of scripts from the database.
    """
    count = await script_repository.count_scripts(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await script_repository.get_paging_scripts(db, skip, limit)
    return PaginationDto(page=page, limit=limit, total=count, data=data)


async def get_scripts_by_status(
    db: AsyncSession, page: int, limit: int, status: str
) -> PaginationDto:
    """
    Get a paginated list of scripts from the database.
    """
    count = await script_repository.count_scripts_by_status(db, status)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await script_repository.get_paging_scripts_by_status(db, skip, limit, status)
    return PaginationDto(page=page, limit=limit, total=count, data=data)


async def get_script_by_id(db: AsyncSession, script_id: str) -> Script:
    """
    Get a script by its ID from the database.
    """
    return await script_repository.get_script_by_id(db, script_id)


async def insert_script(db: AsyncSession, script) -> Script:
    """
    Insert a new script into the database.
    """
    script = Script(
        name=script["name"],
        description=script["description"],
        solution=script["solution"],
        status=script["status"],
    )
    script = await script_repository.insert_script(db, script)
    await db.commit()
    await db.refresh(script)
    return script


async def update_script(db: AsyncSession, script: Script) -> Script:
    """
    Update an existing script in the database.
    """
    await db.commit()
    await db.refresh(script)
    return script


async def delete_script(db: AsyncSession, script_id: str) -> None:
    """
    Delete a script from the database by its ID.
    """
    await script_repository.delete_script(db, script_id)
    await db.commit()


async def delete_multiple_scripts(db: AsyncSession, script_ids: list) -> None:
    """
    Delete multiple scripts from the database by their IDs.
    """
    await script_repository.delete_multiple_scripts(db, script_ids)
    await db.commit()
