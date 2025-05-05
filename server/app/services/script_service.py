import asyncio
import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from app.configs.database import process_background_with_session
from app.dtos import PaginationDto
from app.models import Script
from app.repositories import script_repository
from app.services.integrations import vectordb_service
from fastapi import HTTPException
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

    # Load related sheets as well
    if script:
        # Include both related_scripts and related_sheets
        return script.to_dict(include=["related_scripts", "related_sheets"])

    return None


async def insert_script(db: AsyncSession, script: dict) -> None:
    """
    Insert a new script into the database.
    """
    try:
        script_obj = Script(
            name=script["name"],
            description=script["description"],
            solution=script["solution"],
            status=script["status"],
        )
        script_obj = await script_repository.insert_script(db, script_obj)

        # Xử lý các script liên quan
        related_script_ids = script.get("related_script_ids", [])
        if related_script_ids:
            await script_repository.insert_related_scripts(
                db, script_obj.id, related_script_ids
            )

        # Xử lý các sheet liên quan
        related_sheet_ids = script.get("related_sheet_ids", [])
        if related_sheet_ids:
            await script_repository.insert_related_sheets(
                db, script_obj.id, related_sheet_ids
            )

        await db.commit()

        asyncio.create_task(
            process_background_with_session(
                vectordb_service.insert_script, script_obj.id
            )
        )

        return None
    except Exception as e:
        await db.rollback()
        raise e


async def update_script(db: AsyncSession, script_id: str, script: dict) -> None:
    """
    Update an existing script in the database.
    """
    try:
        existing_script = await script_repository.get_script_by_id(db, script_id)
        if not existing_script:
            raise HTTPException(status_code=404, detail="Script not found")

        # Cập nhật thông tin cơ bản
        existing_script.name = script["name"]
        existing_script.description = script["description"]
        existing_script.solution = script["solution"]
        existing_script.status = script["status"]

        # Cập nhật script trong database
        updated_script = await script_repository.update_script(db, existing_script)

        # Xử lý các script liên quan
        if "related_script_ids" in script:
            new_related_script_ids = set(script.get("related_script_ids", []))

            # Lấy danh sách ID của các script đã liên kết hiện tại
            current_related_script_ids = set()
            if (
                hasattr(existing_script, "related_scripts")
                and existing_script.related_scripts
            ):
                current_related_script_ids = {
                    s.id for s in existing_script.related_scripts
                }

            # Tìm các mối quan hệ cần xóa (có trong hiện tại nhưng không có trong danh sách mới)
            relations_to_delete = current_related_script_ids - new_related_script_ids
            if relations_to_delete:
                await script_repository.delete_related_scripts(
                    db, script_id, list(relations_to_delete)
                )

            # Tìm các mối quan hệ cần thêm (có trong danh sách mới nhưng không có trong hiện tại)
            relations_to_add = new_related_script_ids - current_related_script_ids
            if relations_to_add:
                await script_repository.insert_related_scripts(
                    db, script_id, list(relations_to_add)
                )

        # Xử lý các sheet liên quan
        if "related_sheet_ids" in script:
            new_related_sheet_ids = set(script.get("related_sheet_ids", []))

            # Lấy danh sách ID của các sheet đã liên kết hiện tại
            current_related_sheet_ids = set()
            if hasattr(existing_script, "related_sheets"):
                current_related_sheet_ids = {
                    s.id for s in existing_script.related_sheets
                }

            # Tìm các mối quan hệ cần xóa (có trong hiện tại nhưng không có trong danh sách mới)
            sheet_relations_to_delete = (
                current_related_sheet_ids - new_related_sheet_ids
            )
            if sheet_relations_to_delete:
                await script_repository.delete_related_sheets(
                    db, script_id, list(sheet_relations_to_delete)
                )

            # Tìm các mối quan hệ cần thêm (có trong danh sách mới nhưng không có trong hiện tại)
            sheet_relations_to_add = new_related_sheet_ids - current_related_sheet_ids
            if sheet_relations_to_add:
                await script_repository.insert_related_sheets(
                    db, script_id, list(sheet_relations_to_add)
                )

        await db.commit()

        asyncio.create_task(
            process_background_with_session(
                vectordb_service.update_script, updated_script.id
            )
        )

        # Trả về script với đầy đủ thông tin related
        return None
    except Exception as e:
        await db.rollback()
        raise e


async def delete_script(db: AsyncSession, script_id: str) -> None:
    """
    Delete a script from the database by its ID.
    """
    try:
        await script_repository.delete_script(db, script_id)
        await db.commit()
        asyncio.create_task(vectordb_service.delete_script(script_id))
    except Exception as e:
        await db.rollback()
        raise e


async def delete_multiple_scripts(db: AsyncSession, script_ids: list) -> None:
    """
    Delete multiple scripts from the database by their IDs.
    """
    try:
        await script_repository.delete_multiple_scripts(db, script_ids)
        await db.commit()
        asyncio.create_task(vectordb_service.delete_scripts(script_ids))
    except Exception as e:
        await db.rollback()
        raise e


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
    scripts_with_related = []
    script_id_to_index = {script.id: i + 1 for i, script in enumerate(scripts)}
    for i, script in enumerate(scripts):
        related_ids = [str(script_id_to_index[s.id]) for s in script.related_scripts]

        scripts_with_related.append(
            {
                "id": i + 1,  # Số thứ tự từ 1 đến n
                "name": script.name,
                "related_scripts": ",".join(related_ids) if related_ids else "",
                "status": script.status,
                "description": script.description,
                "solution": script.solution,
            }
        )

    headers_map = {
        "id": "ID",
        "name": "Tên kịch bản",
        "related_scripts": "ID các kịch bản liên quan",
        "status": "Trạng thái",
        "description": "Mô tả",
        "solution": "Hướng dẫn trả lời",
    }

    headers = list(headers_map.values())
    data = [
        {
            headers_map["id"]: script["id"],
            headers_map["name"]: script["name"],
            headers_map["related_scripts"]: script["related_scripts"],
            headers_map["status"]: script["status"],
            headers_map["description"]: script["description"],
            headers_map["solution"]: script["solution"],
        }
        for script in scripts_with_related
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
    - Sheet Excel phải có các cột: "ID", "Tên kịch bản", "ID các kịch bản liên quan", "Trạng thái", "Mô tả", "Hướng dẫn trả lời"
    - Cột ID chỉ là số thứ tự để dễ theo dõi
    - Cột "ID các kịch bản liên quan" chứa danh sách các ID (số thứ tự) được phân cách bằng dấu phẩy
    """
    # Read the Excel file
    try:
        excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")
        headers = [
            "ID",
            "Tên kịch bản",
            "ID các kịch bản liên quan",
            "Trạng thái",
            "Mô tả",
            "Hướng dẫn trả lời",
        ]

        # Kiểm tra các cột bắt buộc
        required_headers = [
            "ID",
            "Tên kịch bản",
            "ID các kịch bản liên quan",
            "Trạng thái",
            "Mô tả",
            "Hướng dẫn trả lời",
        ]
        for header in required_headers:
            if header not in excel_data.columns:
                raise ValueError(f"Thiếu cột {header} trong file Excel")

        # Đầu tiên, tạo và lưu tất cả các script để có ID thực
        scripts: list[Script] = []
        excel_id_at_row_index: list[int] = []
        excel_related_ids_at_index: list[str] = []

        for _, row in excel_data.iterrows():
            excel_id = int(row[headers[0]])  # ID trong Excel (số thứ tự)
            excel_id_at_row_index.append(excel_id)
            script = Script(
                name=row[headers[1]],
                status=row[headers[3]],
                description=row[headers[4]],
                solution=row[headers[5]],
            )
            scripts.append(script)
            # Cột "ID các kịch bản liên quan" bây giờ ở vị trí thứ 3 trong headers (index 2)
            excel_related_ids_at_index.append(
                str(row[headers[2]])
                if headers[2] in row and not pd.isna(row[headers[2]])
                else ""
            )

        # Insert tất cả script vào DB để lấy ID thực
        scripts = await script_repository.insert_scripts(db, scripts)
        parent_and_relateds = {}
        for index, row in excel_data.iterrows():
            related_ids_str = excel_related_ids_at_index[index]

            # Bỏ qua nếu không có ID liên quan
            if pd.isna(related_ids_str) or not related_ids_str.strip():
                continue

            # Lấy script gốc dựa trên ID trong Excel
            parent_script: Script = scripts[index]
            if not parent_script:
                continue

            # Thêm các script liên quan
            related_excel_ids = [
                int(id.strip())
                for id in related_ids_str.split(",")
                if id.strip().isdigit()
            ]
            for related_excel_id in related_excel_ids:
                related_script_index = excel_id_at_row_index.index(related_excel_id)
                related_script = scripts[related_script_index]
                if related_script and related_script != parent_script:
                    if not parent_and_relateds.get(parent_script.id):
                        parent_and_relateds[parent_script.id] = []
                    parent_and_relateds[parent_script.id].append(related_script.id)

        for parent_script_id, related_script_ids in parent_and_relateds.items():
            await script_repository.insert_related_scripts(
                db, parent_script_id, related_script_ids
            )

        await db.commit()

        script_ids = [script.id for script in scripts]

        asyncio.create_task(
            process_background_with_session(vectordb_service.insert_scripts, script_ids)
        )

        return None
    except Exception as e:
        await db.rollback()
        raise e


async def get_all_published_scripts(db: AsyncSession) -> list[Script]:
    """
    Get all published scripts from the database.
    """
    scripts = await script_repository.get_all_scripts_by_status(db, "published")
    return [script.to_dict() for script in scripts] if scripts else []
