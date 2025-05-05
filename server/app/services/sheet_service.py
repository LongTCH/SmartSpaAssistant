import json
import math
import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from app.configs.database import Base
from app.dtos import PaginationDto, PagingDto, SheetColumnConfigDto
from app.models import Sheet
from app.repositories import sheet_repository
from openpyxl.styles import Alignment
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text, text
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
    try:
        # 1. Parse column configuration
        column_config = json.loads(sheet.get("column_config"))
        columns = [
            SheetColumnConfigDto(
                column_name=item.get("column_name"),
                column_type=item.get("column_type"),
                description=item.get("description"),
                is_index=item.get("is_index", False),
            )
            for item in column_config
        ]

        # 2. Create new Sheet record (assuming Sheet is a defined ORM model)
        new_sheet = Sheet(
            name=sheet["name"],
            description=sheet["description"],
            status=sheet["status"],
            column_config=column_config,
        )

        # Insert sheet to get ID
        new_sheet = await sheet_repository.insert_sheet(db, new_sheet)

        # Replace hyphens with underscores in table name for SQL compatibility
        sanitized_table_name = new_sheet.id.replace("-", "_")

        # Set the table_name field
        new_sheet.table_name = sanitized_table_name

        # Kiểm tra xem bảng đã tồn tại chưa
        check_table_sql = text(
            f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = '{sanitized_table_name}'
            )
        """
        )
        result = await db.execute(check_table_sql)
        table_exists = result.scalar()

        if table_exists:
            raise Exception(
                f"Bảng có tên '{sanitized_table_name}' đã tồn tại trong cơ sở dữ liệu"
            )

        # 3. Define SQLAlchemy column types mapping
        type_mapping = {
            "String": String,
            "Text": Text,
            "Integer": Integer,
            "Boolean": Boolean,
            "Numeric": Numeric,
            "DateTime": DateTime,
        }

        # 4. Create list of SQLAlchemy columns
        sqlalchemy_columns = []
        # Add primary key column first - configured as auto-increment
        sqlalchemy_columns.append(
            Column("id", Integer, primary_key=True, autoincrement=True)
        )

        # Create a mapping of column names to their types for later use
        column_type_map = {}

        for col in columns:
            if col.column_type not in type_mapping:
                raise ValueError(
                    f"Unsupported column type: {col.column_type}. Supported types are: {', '.join(type_mapping.keys())}"
                )
            col_type = type_mapping[col.column_type]
            column = Column(
                col.column_name, col_type, index=col.is_index, nullable=True
            )
            sqlalchemy_columns.append(column)
            # Store column type for data conversion
            column_type_map[col.column_name] = col.column_type

        # 5. Dynamically define table class
        DynamicTable = type(
            sanitized_table_name,
            (Base,),
            {
                "__tablename__": sanitized_table_name,
                "__table_args__": {"extend_existing": True},
                **{col.name: col for col in sqlalchemy_columns},
            },
        )

        # 6. Create table in the database using SQLAlchemy properly
        # Use a connection obtained from the session to create the table
        connection = await db.connection()

        # Create the table using run_sync with the connection
        await connection.run_sync(
            lambda sync_conn: DynamicTable.__table__.create(sync_conn, checkfirst=True)
        )

        # Create PGroonga indexes for each String and Text column
        for col in columns:
            # Only create PGroonga indexes for text-based columns
            if col.column_type in ["String", "Text"]:
                index_name = f"pgroonga_{sanitized_table_name}_{col.column_name}_idx"
                index_sql = text(
                    f"""
                    CREATE INDEX "{index_name}" ON "{sanitized_table_name}" 
                    USING pgroonga ("{col.column_name}")
                """
                )
                await db.execute(index_sql)

        # 7. Read Excel file contents
        sheet_file = sheet["file"]
        excel_data = pd.read_excel(BytesIO(sheet_file), engine="openpyxl")

        # Remove 'id' column if it exists in the Excel file
        if "id" in excel_data.columns:
            excel_data = excel_data.drop(columns=["id"])

        # 8. Convert Excel data to list of dictionaries with proper type handling
        rows = []
        for _, row in excel_data.iterrows():
            row_dict = {}
            for col in excel_data.columns:
                # Skip 'id' column (additional check to ensure it's not processed)
                if col.lower() == "id":
                    continue

                value = row[col]

                # Handle missing values
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    row_dict[col] = None
                    continue

                # Check if this column exists in our column_type_map
                if col in column_type_map:
                    col_type = column_type_map[col]

                    # Convert value based on expected column type
                    if col_type == "String" or col_type == "Text":
                        # Convert to string for text columns
                        row_dict[col] = str(value)
                    elif col_type == "Integer":
                        # Handle integers
                        row_dict[col] = (
                            int(float(value))
                            if isinstance(value, (int, float, str))
                            else None
                        )
                    elif col_type == "Numeric":
                        # Handle floating point values
                        row_dict[col] = (
                            float(value)
                            if isinstance(value, (int, float, str))
                            else None
                        )
                    elif col_type == "Boolean":
                        # Handle boolean values
                        if isinstance(value, bool):
                            row_dict[col] = value
                        elif isinstance(value, (int, float)):
                            row_dict[col] = bool(value)
                        elif isinstance(value, str):
                            value = value.lower()
                            row_dict[col] = value in ("yes", "true", "t", "1", "y")
                        else:
                            row_dict[col] = None
                    elif col_type == "DateTime":
                        # Handle datetime values
                        if pd.api.types.is_datetime64_any_dtype(excel_data[col]):
                            row_dict[col] = value if pd.notna(value) else None
                        elif isinstance(value, (datetime, pd.Timestamp)):
                            row_dict[col] = value
                        elif isinstance(value, str):
                            try:
                                # Try parsing string as datetime
                                row_dict[col] = pd.to_datetime(value)
                            except:
                                row_dict[col] = None
                        else:
                            # If it's not a valid datetime value, set to None
                            row_dict[col] = None
                    else:
                        # Default case - just use the raw value
                        row_dict[col] = value
                else:
                    # If column is not in our mapping, just use the raw value
                    row_dict[col] = value

            rows.append(row_dict)

        # 9. Insert rows into the dynamically created table
        # Note: id will be automatically assigned by the database
        if rows:
            db.add_all([DynamicTable(**row) for row in rows])

        # 10. Commit the transaction and refresh the new_sheet instance
        await db.commit()
        await db.refresh(new_sheet)

        return new_sheet.to_dict()

    except Exception as e:
        await db.rollback()
        raise e


async def update_sheet(db: AsyncSession, sheet_id: str, sheet: dict) -> dict:
    """
    Update an existing sheet in the database.
    Only name, description, status, and column descriptions in column_config can be updated.

    Args:
        db: Database session
        sheet_id: ID of the sheet to update
        sheet: Dictionary containing fields to update

    Returns:
        Updated sheet as a dictionary
    """
    # Check if sheet exists
    existing_sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    if not existing_sheet:
        raise Exception(f"Sheet with ID {sheet_id} not found")

    # Prepare update data with only allowed fields
    update_data = {}

    # Allow updating name if provided
    if "name" in sheet:
        update_data["name"] = sheet["name"]

    # Allow updating description if provided
    if "description" in sheet:
        update_data["description"] = sheet["description"]

    # Allow updating status if provided
    if "status" in sheet:
        update_data["status"] = sheet["status"]

    # Handle column_config updates (only descriptions)
    if "column_config" in sheet and isinstance(sheet["column_config"], list):
        # Create a mapping of column names to descriptions from the update data
        column_descriptions = {
            col.get("column_name"): col.get("description")
            for col in sheet["column_config"]
            if col.get("column_name") and col.get("description")
        }

        # Only update if we have valid descriptions to update
        if column_descriptions:
            # Create a deep copy of the existing column config to modify
            updated_column_config = existing_sheet.column_config.copy()

            # Update descriptions for matching columns
            for col in updated_column_config:
                if col["column_name"] in column_descriptions:
                    col["description"] = column_descriptions[col["column_name"]]

            # Set the updated config in update_data
            update_data["column_config"] = updated_column_config

    # Update the sheet using repository function
    updated_sheet = await sheet_repository.update_sheet(db, sheet_id, update_data)

    # Commit the changes
    await db.commit()
    await db.refresh(updated_sheet)

    return updated_sheet.to_dict()


async def delete_sheet(db: AsyncSession, sheet_id: str) -> None:
    """
    Delete a sheet from the database by its ID.
    This function also drops the dynamic table associated with the sheet.
    """
    # Lấy thông tin sheet trước khi xóa
    sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)

    if sheet:
        # 1. Xóa bảng động - sử dụng table_name
        table_name = sheet.table_name
        drop_table_sql = text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

        # Thực hiện xóa bảng
        try:
            await db.execute(drop_table_sql)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"Error dropping table {table_name}: {e}")

    # 2. Xóa bản ghi sheet từ bảng sheets
    await sheet_repository.delete_sheet(db, sheet_id)
    await db.commit()
    return None


async def delete_multiple_sheets(db: AsyncSession, sheet_ids: list[str]) -> None:
    for sheet_id in sheet_ids:
        # Get the sheet to access its table_name
        sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
        if sheet:
            table_name = sheet.table_name
            drop_table_sql = text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

            # Thực hiện xóa bảng
            try:
                await db.execute(drop_table_sql)
                await db.commit()
            except Exception as e:
                await db.rollback()
                print(f"Error dropping table {table_name}: {e}")

    await sheet_repository.delete_multiple_sheets(db, sheet_ids)
    await db.commit()
    return None


async def download_sheet_as_excel(db: AsyncSession, sheet_id: str) -> str:
    """
    Download a sheet as an Excel file using the dynamic table approach.

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

    # Parse the schema from the column config
    columns = [item.get("column_name") for item in sheet.column_config]

    # Ensure columns is a list and not empty
    if not isinstance(columns, list) or len(columns) == 0:
        raise Exception(f"Invalid column configuration for sheet {sheet_id}")

    # Tạo thư mục temp nếu chưa tồn tại
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Tạo tên file với timestamp và tên sheet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{sheet.id}_{timestamp}.xlsx"
    file_path = os.path.join(temp_dir, filename)

    # Get the table name from the sheet record
    table_name = sheet.table_name

    # Dynamically query all rows from the table
    query = text(f'SELECT * FROM "{table_name}" ORDER BY id')
    result = await db.execute(query)
    rows = result.mappings().all()

    # Convert to list of dictionaries
    data_list = [dict(row) for row in rows]

    # Create DataFrame
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
    """
    Get rows from a dynamic sheet table with pagination.

    Args:
        db: Database session
        sheet_id: ID of the sheet/table
        skip: Number of rows to skip
        limit: Maximum number of rows to return

    Returns:
        PagingDto: Paginated sheet rows
    """
    # Get the sheet to verify it exists
    sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    if not sheet:
        raise Exception(f"Sheet with ID {sheet_id} not found")

    # Use the table_name field from the sheet
    table_name = sheet.table_name

    # First count total rows in the table
    count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
    result = await db.execute(count_query)
    count = result.scalar()

    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])

    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])

    # Query rows with pagination
    query = text(f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {skip}')
    result = await db.execute(query)
    rows = result.mappings().all()

    # Convert rows to list of dictionaries
    data_list = [dict(row) for row in rows]

    return PagingDto(skip=skip, limit=limit, total=count, data=data_list)
