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
    # Convert all objects to dictionaries
    data_dict = [script.to_dict() for script in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


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
    # Convert all objects to dictionaries
    data_dict = [script.to_dict() for script in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_script_by_id(db: AsyncSession, script_id: str) -> dict:
    """
    Get a script by its ID from the database.
    """
    script = await script_repository.get_script_by_id(db, script_id)
    return script.to_dict() if script else None


async def insert_script(db: AsyncSession, script: dict) -> dict:
    """
    Insert a new script into the database.
    """
    script_obj = Script(
        name=script["name"],
        description=script["description"],
        solution=script["solution"],
        status=script["status"],
    )
    script_obj = await script_repository.insert_script(db, script_obj)
    await db.commit()
    await db.refresh(script_obj)
    return script_obj.to_dict()


async def update_script(db: AsyncSession, script_id: str, script: dict) -> dict:
    """
    Update an existing script in the database.
    """
    existing_script = await script_repository.get_script_by_id(db, script_id)
    if not existing_script:
        return None
    existing_script.name = script["name"]
    existing_script.description = script["description"]
    existing_script.solution = script["solution"]
    existing_script.status = script["status"]
    updated_script = await script_repository.update_script(db, existing_script)
    await db.commit()
    await db.refresh(updated_script)
    return updated_script.to_dict()


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
