import json
import math
import os
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
from app.dtos import PaginationDto, PagingDto
from app.models import Sheet, SheetRow
from app.repositories import sheet_repository, sheet_row_repository
from openpyxl.styles import Alignment
from sqlalchemy.ext.asyncio import AsyncSession


async def get_sheets(db: AsyncSession, page: int, limit: int) -> PaginationDto:
    """
    Get a paginated list of sheets from the database.
    """
    count = await sheet_repository.count_sheets(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])

    skip = (page - 1) * limit
    data = await sheet_repository.get_paging_sheets(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [sheet.to_dict() for sheet in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_sheets_by_status(
    db: AsyncSession, page: int, limit: int, status: str
) -> PaginationDto:
    """
    Get a paginated list of sheets from the database by status.
    """
    count = await sheet_repository.count_sheets_by_status(db, status)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])

    skip = (page - 1) * limit
    data = await sheet_repository.get_paging_sheets_by_status(db, skip, limit, status)
    # Convert all objects to dictionaries
    data_dict = [sheet.to_dict() for sheet in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_sheet_by_id(db: AsyncSession, sheet_id: str) -> dict:
    """
    Get a sheet by its ID from the database.
    """
    sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    return sheet.to_dict() if sheet else None


async def insert_sheet(db: AsyncSession, sheet: dict) -> dict:
    """
    Insert a new sheet into the database.

    Parameters:
    - sheet: Dictionary containing sheet data with keys:
        - name: Name of the sheet
        - description: Description of the sheet
        - status: Status of the sheet
        - file: Excel file contents as bytes

    Returns:
    - dict: The created Sheet object as a dictionary
    """
    try:
        # Extract file contents
        sheet_file = sheet["file"]

        # Read Excel file contents
        excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")

        # Get headers and convert to schema
        headers = list(excel_data.columns)
        schema = json.dumps(headers, ensure_ascii=False)

        # Convert Excel data to list of dictionaries and handle Timestamp objects
        rows = []
        for _, row in excel_data.iterrows():
            row_dict = {}
            for col in excel_data.columns:
                value = row[col]

                # Handle NaN values
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    row_dict[col] = None
                # Convert Timestamp objects to ISO format strings
                elif pd.api.types.is_datetime64_any_dtype(excel_data[col]):
                    row_dict[col] = value.isoformat() if pd.notna(value) else None
                # Handle numpy numeric types
                elif isinstance(value, (np.integer, np.floating)):
                    row_dict[col] = (
                        int(value) if isinstance(value, np.integer) else float(value)
                    )
                else:
                    row_dict[col] = value

            rows.append(row_dict)

        # Create new Sheet record
        new_sheet = Sheet(
            name=sheet["name"],
            description=sheet["description"],
            status=sheet["status"],
            schema=schema,
            # first row for sample
            sample_rows=json.dumps(rows[0] if rows else {}, ensure_ascii=False),
        )

        # Insert sheet to get ID
        new_sheet = await sheet_repository.insert_sheet(db, new_sheet)

        # Create SheetRow records
        sheet_rows = []
        # Use enumerate for efficient index tracking and list comprehension for optimized creation
        sheet_rows = [
            SheetRow(sheet_id=new_sheet.id, order=idx, data=row_data)
            for idx, row_data in enumerate(rows)
        ]

        # Insert all sheet rows
        if sheet_rows:
            await sheet_row_repository.insert_or_update(db, sheet_rows)

        # Commit the transaction
        await db.commit()
        await db.refresh(new_sheet)

        return new_sheet.to_dict()

    except Exception as e:
        # Rollback in case of error
        await db.rollback()
        raise e


async def update_sheet(db: AsyncSession, sheet_id: str, sheet: dict) -> dict:
    """
    Update an existing sheet in the database.
    """
    # Get the existing sheet
    existing_sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    if not existing_sheet:
        raise Exception(f"Sheet with ID {sheet_id} not found")

    # Update the sheet attributes
    existing_sheet.name = sheet.get("name", existing_sheet.name)
    existing_sheet.description = sheet.get("description", existing_sheet.description)
    existing_sheet.status = sheet.get("status", existing_sheet.status)

    # Commit the changes
    await db.commit()
    await db.refresh(existing_sheet)

    return existing_sheet.to_dict()


async def delete_sheet(db: AsyncSession, sheet_id: str) -> None:
    """
    Delete a sheet from the database by its ID.
    """
    await sheet_repository.delete_sheet(db, sheet_id)
    await db.commit()
    return None


async def delete_multiple_sheets(db: AsyncSession, sheet_ids: list[str]) -> None:
    """
    Delete multiple sheets from the database by their IDs.
    """
    await sheet_repository.delete_multiple_sheets(db, sheet_ids)
    await db.commit()
    return None


async def download_sheet_as_excel(db: AsyncSession, sheet_id: str) -> str:
    """
    Download a sheet as an Excel file.

    Args:
        db: Database session
        sheet_id: ID of the sheet to download

    Returns:
        str: Đường dẫn đến file Excel đã lưu trên ổ đĩa
    """
    # Get the sheet with its schema
    sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    if not sheet:
        raise Exception(f"Sheet with ID {sheet_id} not found")

    # Get all rows for this sheet
    sheet_rows = await sheet_row_repository.get_all_sheet_rows_by_sheet_id(db, sheet_id)

    # Ensure we have valid headers from the schema
    # The schema is already a JSON string, so we just need to parse it
    try:
        headers = json.loads(sheet.schema)
    except json.JSONDecodeError:
        # If we can't parse the schema, use an empty list
        headers = []

    # Ensure headers is a list
    if not isinstance(headers, list):
        headers = [] if not headers else [headers]

    # Tạo thư mục temp nếu chưa tồn tại
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Tạo tên file với timestamp và tên sheet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{sheet.id}_{timestamp}.xlsx"
    file_path = os.path.join(temp_dir, filename)

    # Tạo DataFrame từ dữ liệu
    data_list = []
    for row_data in sheet_rows:
        # Handle the case where row_data.data is stored as a JSON string
        data = row_data.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If we can't parse it as JSON, use an empty dict
                data = {}

        # Make sure data is a dictionary
        if not isinstance(data, dict):
            data = {}

        row_dict = {header: data.get(header, "") for header in headers}
        data_list.append(row_dict)

    df = pd.DataFrame(data_list)

    # Lưu DataFrame thành file Excel
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet.name)

        # Điều chỉnh chiều rộng cột
        worksheet = writer.sheets[sheet.name]
        # Set headers alignment to left
        for cell in worksheet[1]:
            cell.alignment = Alignment(horizontal="left")
        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

    return file_path


async def get_sheet_rows_by_sheet_id(
    db: AsyncSession, sheet_id: str, skip: int, limit: int
) -> PagingDto:

    count = await sheet_row_repository.count_sheet_rows_by_sheet_id(db, sheet_id)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await sheet_row_repository.get_sheet_row_by__sheet_id(
        db, sheet_id, skip, limit
    )
    # Convert all objects to dictionaries
    data_dict = [row.data for row in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)
