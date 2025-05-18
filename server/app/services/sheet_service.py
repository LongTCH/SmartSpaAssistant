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
from app.utils.excel_utils import adjust_column_widths_in_worksheet
from openpyxl.styles import Alignment
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified


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


async def insert_sheet(db: AsyncSession, sheet: dict) -> str:
    try:
        # Parse column configuration
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
        sheet_file = sheet["file"]

        # If user requested information about available sheets, return that instead
        if sheet.get("get_sheet_names", False):
            # Read all sheet names from the Excel file
            xls = pd.ExcelFile(BytesIO(sheet_file))
            return {"sheet_names": xls.sheet_names}

        # Check available sheets in the Excel file
        xls = pd.ExcelFile(BytesIO(sheet_file))
        available_sheets = xls.sheet_names

        # Priority order for reading sheets:
        # 1. Use sheet_name from request if provided
        # 2. Use 'data' sheet if it exists
        # 3. Fall back to the first sheet (index 0)
        if sheet.get("sheet_name"):
            sheet_name = sheet.get("sheet_name")
        elif "data" in available_sheets:
            sheet_name = "data"
        else:
            sheet_name = 0  # Default to first sheet

        # Read the Excel file with the selected sheet
        excel_data = pd.read_excel(
            BytesIO(sheet_file), engine="openpyxl", sheet_name=sheet_name
        )

        # Define SQLAlchemy column types mapping
        type_mapping = {
            "String": String,
            "Text": Text,
            "Integer": Integer,
            "Boolean": Boolean,
            "Numeric": Numeric,
            "DateTime": DateTime,
        }
        # Create list of SQLAlchemy columns
        sqlalchemy_columns = []
        sqlalchemy_columns.append(Column("id", Integer, primary_key=True))
        # Create a mapping of column names to their types for later use
        column_type_map = {}

        for col in columns:
            if col.column_type not in type_mapping:
                raise ValueError(
                    f"Unsupported column type: {col.column_type}. Supported types are: {', '.join(type_mapping.keys())}"
                )
            if col.column_name == "id":
                continue  # Skip 'id' column as it's already added
            col_type = type_mapping[col.column_type]
            column = Column(
                col.column_name, col_type, index=col.is_index, nullable=True
            )
            sqlalchemy_columns.append(column)
            # Store column type for data conversion
            column_type_map[col.column_name] = col.column_type
        # Convert Excel data to list of dictionaries with proper type handling
        rows = []
        for _, row in excel_data.iterrows():
            row_dict = {}
            for col in excel_data.columns:
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

        # Validate that we have 'id' column with type Integer in column_config
        if not any(
            col.column_name == "id" and col.column_type == "Integer" for col in columns
        ):
            raise ValueError(
                "Column 'id' with type Integer is required in column_config"
            )
        # Validate that data of 'id' column is unique
        id_values = [row["id"] for row in rows if "id" in row]
        if len(id_values) != len(set(id_values)):
            raise ValueError("Duplicate values found in 'id' column")
        # Validate that 'id' column is not null or empty
        if any(row["id"] is None or row["id"] == "" for row in rows):
            raise ValueError("Null or empty values found in 'id' column")

        # Create new Sheet record (assuming Sheet is a defined ORM model)
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

        # Dynamically define table class
        DynamicTable = type(
            sanitized_table_name,
            (Base,),
            {
                "__tablename__": sanitized_table_name,
                "__table_args__": {"extend_existing": True},
                **{col.name: col for col in sqlalchemy_columns},
            },
        )

        # Create table in the database using SQLAlchemy properly
        # Use a connection obtained from the session to create the table
        connection = await db.connection()

        # Create the table using run_sync with the connection
        await connection.run_sync(
            lambda sync_conn: DynamicTable.__table__.create(sync_conn, checkfirst=True)
        )

        # Create PGroonga indexes on all String and Text columns for better text search performance
        for col in columns:
            if col.column_type in ["String", "Text"]:
                col_index_name = (
                    f"pgroonga_{sanitized_table_name}_{col.column_name}_idx"
                )
                col_index_sql = text(
                    f"""
                    CREATE INDEX "{col_index_name}" ON "{sanitized_table_name}" 
                    USING pgroonga ("{col.column_name}")
                """
                )
                await db.execute(col_index_sql)

        # Insert rows into the dynamically created table
        # Note: id will be automatically assigned by the database
        if rows:
            db.add_all([DynamicTable(**row) for row in rows])

        # Commit the transaction and refresh the new_sheet instance
        await db.commit()
        await db.refresh(new_sheet)

        return new_sheet.id

    except Exception as e:
        await db.rollback()
        raise e


async def update_sheet(db: AsyncSession, sheet_id: str, sheet: dict) -> None:
    try:
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
                updated_column_config = existing_sheet.column_config

                # Update descriptions for matching columns
                for col in updated_column_config:
                    if col["column_name"] in column_descriptions:
                        col["description"] = column_descriptions[col["column_name"]]

            flag_modified(existing_sheet, "column_config")
        # Update the sheet using repository function
        await sheet_repository.update_sheet(db, existing_sheet)

        # Commit the changes
        await db.commit()

        return None
    except Exception as e:
        await db.rollback()
        raise e


async def delete_sheet(db: AsyncSession, sheet_id: str) -> None:
    """
    Delete a sheet from the database by its ID.
    This function also drops the dynamic table associated with the sheet.
    """
    try:
        sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)

        if sheet:
            # 1. Xóa bảng động - sử dụng table_name
            table_name = sheet.table_name
            drop_table_sql = text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

            await db.execute(drop_table_sql)

        # 2. Xóa bản ghi sheet từ bảng sheets
        await sheet_repository.delete_sheet(db, sheet_id)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        raise e


async def delete_multiple_sheets(db: AsyncSession, sheet_ids: list[str]) -> None:
    try:
        for sheet_id in sheet_ids:
            # Get the sheet to access its table_name
            sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
            if sheet:
                table_name = sheet.table_name
                drop_table_sql = text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

                await db.execute(drop_table_sql)

        await sheet_repository.delete_multiple_sheets(db, sheet_ids)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        raise e


async def download_sheet_as_excel(db: AsyncSession, sheet_id: str) -> str:
    """
    Download a sheet as an Excel file.
    The Excel file will contain three sheets:
    1. 'data': Contains the main table data.
    2. 'sheet_info': Contains the table name and description.
    3. 'column_config': Contains the configuration for each column.

    Args:
        db: Database session
        sheet_id: ID of the sheet to download

    Returns:
        str: Path to the saved Excel file.
    """
    # Get the sheet with its schema
    sheet = await sheet_repository.get_sheet_by_id(db, sheet_id)
    if not sheet:
        raise Exception(f"Sheet with ID {sheet_id} not found")

    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Create filename with timestamp and a sanitized sheet name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sane_sheet_name = "".join(c if c.isalnum() else "_" for c in sheet.name)
    filename = f"{sane_sheet_name}_{sheet.id}_{timestamp}.xlsx"
    file_path = os.path.join(temp_dir, filename)

    # --- Prepare 'data' sheet ---
    data_columns = [item.get("column_name") for item in sheet.column_config]
    if not isinstance(data_columns, list) or not data_columns:
        raise Exception(f"Invalid or empty column configuration for sheet {sheet_id}")

    table_name = sheet.table_name
    rows = await sheet_repository.get_all_rows_with_sheet_and_columns(
        db, table_name, data_columns
    )
    data_list = [dict(row) for row in rows]
    df_data = pd.DataFrame(data_list)
    # Ensure columns in DataFrame match data_columns, even if data_list is empty
    if df_data.empty and data_columns:
        df_data = pd.DataFrame(columns=data_columns)

    # --- Prepare 'sheet_info' sheet ---
    sheet_info_data = {
        "field": ["table", "description"],
        "value": [sheet.name, sheet.description],
    }
    df_sheet_info = pd.DataFrame(sheet_info_data)

    # --- Prepare 'column_config' sheet ---
    column_config_list = []
    for config_item in sheet.column_config:
        column_config_list.append(
            {
                "column_name": config_item.get("column_name"),
                "column_type": config_item.get("column_type"),
                "description": config_item.get("description"),
                "is_index": config_item.get("is_index", False),
            }
        )
    df_column_config = pd.DataFrame(column_config_list)
    # Ensure the correct columns and order
    if not df_column_config.empty:
        df_column_config = df_column_config[
            ["column_name", "column_type", "description", "is_index"]
        ]
    else:  # Handle empty column_config case
        df_column_config = pd.DataFrame(
            columns=["column_name", "column_type", "description", "is_index"]
        )

    # Helper function to adjust column widths

    # Write DataFrames to Excel file
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # Write 'data' sheet
        df_data.to_excel(writer, index=False, sheet_name="data")
        worksheet_data = writer.sheets["data"]
        for cell in worksheet_data[1]:  # Header row
            cell.alignment = Alignment(horizontal="left")
        if not df_data.empty:
            adjust_column_widths_in_worksheet(worksheet_data, df_data)

        # Write 'sheet_info' sheet
        df_sheet_info.to_excel(writer, index=False, sheet_name="sheet_info")
        worksheet_sheet_info = writer.sheets["sheet_info"]
        if not df_sheet_info.empty:
            adjust_column_widths_in_worksheet(worksheet_sheet_info, df_sheet_info)
            for cell in worksheet_sheet_info[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")

        # Write 'column_config' sheet
        df_column_config.to_excel(writer, index=False, sheet_name="column_config")
        worksheet_column_config = writer.sheets["column_config"]
        if not df_column_config.empty:
            adjust_column_widths_in_worksheet(worksheet_column_config, df_column_config)
            for cell in worksheet_column_config[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")

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
    count = await sheet_repository.count_rows_of_sheet(db, table_name)

    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])

    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])

    columns = [item.get("column_name") for item in sheet.column_config]
    rows = await sheet_repository.get_rows_with_columns(
        db, table_name, columns, skip, limit
    )

    # Convert rows to list of dictionaries
    data_list = [dict(row) for row in rows]

    return PagingDto(skip=skip, limit=limit, total=count, data=data_list)
