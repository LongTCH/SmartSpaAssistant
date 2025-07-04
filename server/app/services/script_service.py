import xml.etree.ElementTree as ET
from io import BytesIO

import pandas as pd
from app.dtos import PaginationDto
from app.models import Script
from app.repositories import script_repository
from app.utils.excel_utils import adjust_column_widths_in_worksheet
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
        # Include both related_scripts
        return script.to_dict(include=["related_scripts"])

    return None


async def insert_script(db: AsyncSession, script: dict) -> str:
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

        await db.commit()

        return script_obj.id
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

        await db.commit()

        return updated_script.id
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
    except Exception as e:
        await db.rollback()
        raise e


async def download_scripts_as_excel_stream(db: AsyncSession) -> BytesIO:
    """
    Download all scripts as an Excel file stream (BytesIO).
    """
    scripts = await script_repository.get_all_scripts(db)
    if not scripts:
        return None

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

    # Create BytesIO buffer
    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
        worksheet = writer.sheets["data"]
        # Set headers alignment to left
        for cell in worksheet[1]:
            cell.alignment = Alignment(horizontal="left")
        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    excel_buffer.seek(0)  # Reset to beginning of buffer
    return excel_buffer


async def insert_scripts_from_excel(db: AsyncSession, sheet_file) -> list[str]:
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

        return script_ids
    except Exception as e:
        await db.rollback()
        raise e


async def get_all_published_scripts(db: AsyncSession) -> list[Script]:
    """
    Get all published scripts from the database.
    """
    scripts = await script_repository.get_all_scripts_by_status(db, "published")
    return [script.to_dict() for script in scripts] if scripts else []


async def get_script_template() -> BytesIO:
    """
    Generate a template Excel file for scripts as BytesIO.
    The template will contain sample data with required columns.

    Returns:
        BytesIO: Excel file contents in a BytesIO buffer.
    """
    try:
        # Sample data
        data_list = [
            {
                "ID": 1,
                "Tên kịch bản": "Thông tin sản phẩm vay",
                "ID các kịch bản liên quan": "",
                "Trạng thái": "published",
                "Mô tả": '"lãi suất", "thời hạn vay", "điều kiện vay"',
                "Hướng dẫn trả lời": "Giải thích về lãi suất, thời hạn vay và điều kiện vay.",
            },
            {
                "ID": 2,
                "Tên kịch bản": "Thủ tục đăng ký thẻ tín dụng",
                "ID các kịch bản liên quan": "1",
                "Trạng thái": "published",
                "Mô tả": '"đăng ký như thế nào", "cần giấy tờ gì"',
                "Hướng dẫn trả lời": "Hướng dẫn khách hàng cách đăng ký thẻ tín dụng, giấy tờ cần thiết và thời gian xử lý.",
            },
            {
                "ID": 3,
                "Tên kịch bản": "Chính sách ưu đãi khách hàng mới",
                "ID các kịch bản liên quan": "1,2",
                "Trạng thái": "draft",
                "Mô tả": '"có giảm giá không", "có ưu đãi gì không"',
                "Hướng dẫn trả lời": "Giới thiệu các chương trình ưu đãi hiện tại, thời gian áp dụng và điều kiện.",
            },
        ]
        df_data = pd.DataFrame(data_list)

        excel_buffer = BytesIO()
        # Write to Excel file
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            # Write data sheet
            df_data.to_excel(writer, index=False, sheet_name="data")
            worksheet_data = writer.sheets["data"]
            for cell in worksheet_data[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")
            adjust_column_widths_in_worksheet(worksheet_data, df_data)

        excel_buffer.seek(0)  # Reset buffer position to the beginning
        return excel_buffer
    except Exception as e:
        # Log the exception for more details if needed
        print(f"Error generating script template: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating script template: {str(e)}"
        )


async def agent_scripts_to_xml(scripts: list[Script]) -> str:
    root = ET.Element("scripts")

    for script in scripts:
        script_elem = ET.SubElement(root, "script")

        questions_elem = ET.SubElement(script_elem, "questions")

        # Split description by newlines and create question elements
        question_lines = script.description.split("\n")
        for question_line in question_lines:
            question_line = question_line.strip()
            if question_line:  # Only add non-empty questions
                question_elem = ET.SubElement(questions_elem, "question")
                question_elem.text = question_line

        information = ET.SubElement(script_elem, "information")
        information.text = script.solution

    return ET.tostring(root, encoding="unicode")
