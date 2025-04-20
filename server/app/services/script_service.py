import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from app.dtos import PaginationDto
from app.models import Script
from app.repositories import script_repository
from openpyxl.styles import Alignment
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


async def download_scripts_as_excel(db: AsyncSession) -> str:
    """
    Download all scripts as an Excel file.
    """
    scripts = await script_repository.get_all_scripts(db)
    if not scripts:
        return None

    # Tạo thư mục temp nếu chưa tồn tại
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scripts_{timestamp}.xlsx"
    file_path = os.path.join(temp_dir, filename)

    headers_map = {
        "name": "Tên kịch bản",
        "status": "Trạng thái",
        "description": "Mô tả",
        "solution": "Hướng dẫn trả lời",
    }

    headers = list(headers_map.values())
    data = [
        {
            headers_map["name"]: script.name,
            headers_map["status"]: script.status,
            headers_map["description"]: script.description,
            headers_map["solution"]: script.solution,
        }
        for script in scripts
    ]

    df = pd.DataFrame(data, columns=headers)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Kịch bản")
        worksheet = writer.sheets["Kịch bản"]
        # Set headers alignment to left
        for cell in worksheet[1]:
            cell.alignment = Alignment(horizontal="left")
        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    return file_path


async def insert_scripts_from_excel(db: AsyncSession, sheet_file) -> None:
    """
    Insert scripts from an Excel file into the database.
    """
    # Read the Excel file
    excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")
    headers = ["Tên kịch bản", "Trạng thái", "Mô tả", "Hướng dẫn trả lời"]

    scripts: list[Script] = []
    for _, row in excel_data.iterrows():
        script = Script(
            name=row[headers[0]],
            status=row[headers[1]],
            description=row[headers[2]],
            solution=row[headers[3]],
        )
        scripts.append(script)
    await script_repository.insert_or_update_scripts(db, scripts)
    await db.commit()
    return None
