from io import BytesIO

import pandas as pd
from app.dtos import PaginationDto
from app.models import Interest
from app.repositories import interest_repository
from app.utils.excel_utils import adjust_column_widths_in_worksheet
from fastapi import HTTPException
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


async def insert_interest(db: AsyncSession, interest: dict) -> None:
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
        return None
    except Exception as e:
        await db.rollback()
        raise e


async def update_interest(db: AsyncSession, interest_id: str, interest: dict) -> None:
    """
    Update an existing interest in the database.
    """
    try:
        existing_interest = await interest_repository.get_interest_by_id(
            db, interest_id
        )
        if not existing_interest:
            raise HTTPException(status_code=404, detail="Interest not found")
        existing_interest.name = interest["name"]
        existing_interest.related_terms = interest["related_terms"]
        existing_interest.status = interest["status"]
        existing_interest.color = interest["color"]
        updated_interest = await interest_repository.update_interest(
            db, existing_interest
        )
        await db.commit()

        return None
    except Exception as e:
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
        await db.rollback()
        raise e


async def download_interests_as_excel(db: AsyncSession) -> BytesIO:
    """
    Download all interests as an Excel file.
    """
    interests = await interest_repository.get_all_interests(db)
    if not interests:
        return None

    headers_map = {
        "name": "Nhãn",
        "related_terms": "Các từ khóa",
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
    excel_buffer.seek(0)
    return excel_buffer


async def insert_interests_from_excel(db: AsyncSession, sheet_file) -> None:
    """
    Insert interests from an Excel file into the database.
    """
    # Read the Excel file
    try:
        excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")
        headers = ["Nhãn", "Các từ khóa", "Trạng thái", "Mã màu"]

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
        await db.rollback()
        raise e


async def get_interest_template() -> BytesIO:
    """
    Generate a template Excel file for interests.
    The template will contain sample data with required columns.

    Returns:
        str: Path to the template Excel file
    """
    try:
        # Sample data
        data_list = [
            {
                "Nhãn": "Sản phẩm tiết kiệm",
                "Các từ khóa": "tiết kiệm, lãi suất, kỳ hạn",
                "Trạng thái": "published",
                "Mã màu": "#3498db",
            },
            {
                "Nhãn": "Vay mua nhà",
                "Các từ khóa": "thế chấp, lãi suất vay, bất động sản",
                "Trạng thái": "draft",
                "Mã màu": "#e74c3c",
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

        excel_buffer.seek(0)
        return excel_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_all_interests_by_status(db: AsyncSession, status: str) -> list:
    """
    Get all interests by status from the database.
    """
    interests = await interest_repository.get_interests_by_status(db, status)
    return [interest.to_dict() for interest in interests] if interests else []


async def get_interest_ids_from_text(db: AsyncSession, text: str) -> list[str]:
    """
    Get interest IDs from a given text and associate them with a guest.
    """
    try:
        if not text:
            return []

        # Convert text to lowercase for case-insensitive matching
        text = text.lower() if isinstance(text, str) else str(text).lower()

        # Get all interests in a single query
        interests = await interest_repository.get_interests_by_status(db, "published")
        if not interests:
            return []

        # Find matching interests
        interest_ids = []
        for interest in interests:
            keywords = []
            if interest.name:
                keywords.append(interest.name.lower())

            if interest.related_terms:
                keywords.extend(
                    [
                        kw.strip().lower()
                        for kw in interest.related_terms.split(",")
                        if kw.strip()
                    ]
                )

            # Check if any keyword is in the text
            if any(kw in text for kw in keywords if kw):
                interest_ids.append(interest.id)

        return interest_ids
    except Exception as e:
        print(f"Error in add_interest_ids_from_text: {e}")
        return []
