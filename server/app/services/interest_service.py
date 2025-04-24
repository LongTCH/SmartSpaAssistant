import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from app.dtos import PaginationDto
from app.models import Interest
from app.repositories import interest_repository
from openpyxl.styles import Alignment
from sqlalchemy.ext.asyncio import AsyncSession


async def get_interests(db: AsyncSession, page: int, limit: int) -> PaginationDto:
    """
    Get a paginated list of interests from the database.
    """
    count = await interest_repository.count_interests(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await interest_repository.get_paging_interests(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [interest.to_dict() for interest in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_interests_by_status(
    db: AsyncSession, page: int, limit: int, status: str
) -> PaginationDto:
    """
    Get a paginated list of interests from the database.
    """
    count = await interest_repository.count_interests_by_status(db, status)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await interest_repository.get_paging_interests_by_status(
        db, skip, limit, status
    )
    # Convert all objects to dictionaries
    data_dict = [interest.to_dict() for interest in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_interest_by_id(db: AsyncSession, interest_id: str) -> dict:
    """
    Get a interest by its ID from the database.
    """
    interest = await interest_repository.get_interest_by_id(db, interest_id)
    return interest.to_dict() if interest else None


async def insert_interest(db: AsyncSession, interest: dict) -> dict:
    """
    Insert a new interest into the database.
    """
    try:
        interest_obj = Interest(
            name=interest["name"],
            related_terms=interest["related_terms"],
            status=interest["status"],
            color=interest["color"],
        )
        interest_obj = await interest_repository.insert_interest(db, interest_obj)
        await db.commit()
        await db.refresh(interest_obj)
        return interest_obj.to_dict()
    except Exception as e:
        print(f"Error inserting interest: {e}")
        await db.rollback()
        raise e


async def update_interest(db: AsyncSession, interest_id: str, interest: dict) -> dict:
    """
    Update an existing interest in the database.
    """
    try:
        existing_interest = await interest_repository.get_interest_by_id(
            db, interest_id
        )
        if not existing_interest:
            return None
        existing_interest.name = interest["name"]
        existing_interest.related_terms = interest["related_terms"]
        existing_interest.status = interest["status"]
        existing_interest.color = interest["color"]
        updated_interest = await interest_repository.update_interest(
            db, existing_interest
        )
        await db.commit()
        await db.refresh(updated_interest)

        return updated_interest.to_dict()
    except Exception as e:
        print(f"Error updating interest: {e}")
        await db.rollback()
        raise e


async def delete_interest(db: AsyncSession, interest_id: str) -> None:
    """
    Delete a interest from the database by its ID.
    """
    try:
        await interest_repository.delete_interest(db, interest_id)
        await db.commit()
    except Exception as e:
        print(f"Error deleting interest: {e}")
        await db.rollback()
        raise e


async def delete_multiple_interests(db: AsyncSession, interest_ids: list) -> None:
    """
    Delete multiple interests from the database by their IDs.
    """
    try:
        await interest_repository.delete_multiple_interests(db, interest_ids)
        await db.commit()
    except Exception as e:
        print(f"Error deleting multiple interests: {e}")
        await db.rollback()
        raise e


async def download_interests_as_excel(db: AsyncSession) -> str:
    """
    Download all interests as an Excel file.
    """
    interests = await interest_repository.get_all_interests(db)
    if not interests:
        return None

    # Tạo thư mục temp nếu chưa tồn tại
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"interests_{timestamp}.xlsx"
    file_path = os.path.join(temp_dir, filename)

    headers_map = {
        "name": "Từ khóa",
        "related_terms": "Các từ liên quan",
        "status": "Trạng thái",
        "color": "Mã màu",
    }

    headers = list(headers_map.values())
    data = [
        {
            headers_map["name"]: interest.name,
            headers_map["related_terms"]: interest.related_terms,
            headers_map["status"]: interest.status,
            headers_map["color"]: interest.color,
        }
        for interest in interests
    ]

    df = pd.DataFrame(data, columns=headers)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Xu hướng")
        worksheet = writer.sheets["Xu hướng"]
        # Set headers alignment to left
        for cell in worksheet[1]:
            cell.alignment = Alignment(horizontal="left")
        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    return file_path


async def insert_interests_from_excel(db: AsyncSession, sheet_file) -> None:
    """
    Insert interests from an Excel file into the database.
    """
    # Read the Excel file
    try:
        excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")
        headers = ["Từ khóa", "Các từ liên quan", "Trạng thái", "Mã màu"]

        interests: list[Interest] = []
        for _, row in excel_data.iterrows():
            interest = Interest(
                name=row[headers[0]],
                related_terms=row[headers[1]],
                status=row[headers[2]],
                color=row[headers[3]],
            )
            interests.append(interest)
        await interest_repository.insert_or_update_interests(db, interests)
        await db.commit()
        return None
    except Exception as e:
        print(f"Error inserting interests from Excel: {e}")
        await db.rollback()
        raise e


async def get_all_interests_by_status(db: AsyncSession, status: str) -> list:
    """
    Get all interests by status from the database.
    """
    interests = await interest_repository.get_interests_by_status(db, status)
    return [interest.to_dict() for interest in interests] if interests else []
