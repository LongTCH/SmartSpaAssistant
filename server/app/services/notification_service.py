from datetime import datetime
from io import BytesIO

import pandas as pd
from app.dtos import PaginationDto
from app.models import Notification
from app.repositories import notification_repository
from app.utils.excel_utils import adjust_column_widths_in_worksheet
from fastapi import HTTPException
from openpyxl.styles import Alignment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified


async def get_notifications(db: AsyncSession, page: int, limit: int) -> PaginationDto:
    """
    Get a paginated list of notifications from the database.
    """
    count = await notification_repository.count_notifications(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await notification_repository.get_paging_notifications(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [notification.to_dict() for notification in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_notifications_by_status(
    db: AsyncSession, page: int, limit: int, status: str
) -> PaginationDto:
    """
    Get a paginated list of notifications from the database.
    """
    count = await notification_repository.count_notifications_by_status(db, status)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await notification_repository.get_paging_notifications_by_status(
        db, skip, limit, status
    )
    # Convert all objects to dictionaries
    data_dict = [notification.to_dict() for notification in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_notification_by_id(db: AsyncSession, notification_id: str) -> dict:
    """
    Get a notification by its ID from the database.
    """
    notification = await notification_repository.get_notification_by_id(
        db, notification_id
    )
    return notification.to_dict() if notification else None


async def insert_notification(db: AsyncSession, notification: dict) -> None:
    """
    Insert a new notification into the database.
    """
    try:
        # Validate params if present
        params = notification.get("params", [])
        if params:
            # Ensure params is a list
            if not isinstance(params, list):
                raise HTTPException(status_code=400, detail="Params must be a list")

            # Check for valid index values
            index_values = []
            for i, param in enumerate(params):
                if not isinstance(param, dict):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Param at position {i} must be an object",
                    )

                # Ensure index is present and is an integer
                index_val = param.get("index")
                if index_val is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing index in param at position {i}",
                    )

                # Convert string indices to integers if possible
                if isinstance(index_val, str) and index_val.isdigit():
                    index_val = int(index_val)
                    param["index"] = index_val

                if not isinstance(index_val, int):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Index must be an integer, found: {index_val}",
                    )

                index_values.append(index_val)

            # Check for duplicate indices
            if len(index_values) != len(set(index_values)):
                duplicates = [x for x in index_values if index_values.count(x) > 1]
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate index values found: {set(duplicates)}",
                )

        notification_obj = Notification(
            label=notification.get("label"),
            status=notification.get("status"),
            color=notification.get("color"),
            description=notification.get("description"),
            params=params,
            content=notification.get("content"),
            created_at=datetime.now(),
        )
        await notification_repository.insert_notification(db, notification_obj)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_notification(
    db: AsyncSession, notification_id: str, notification: dict
) -> None:
    """
    Update an existing notification in the database.
    """
    try:
        notification_obj = await notification_repository.get_notification_by_id(
            db, notification_id
        )
        if not notification_obj:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Validate params if present
        params = notification.get("params")
        if params is not None:
            # Ensure params is a list
            if not isinstance(params, list):
                raise HTTPException(status_code=400, detail="Params must be a list")

            # Check for valid index values
            index_values = []
            for i, param in enumerate(params):
                if not isinstance(param, dict):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Param at position {i} must be an object",
                    )

                # Ensure index is present and is an integer
                index_val = param.get("index")
                if index_val is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing index in param at position {i}",
                    )

                # Convert string indices to integers if possible
                if isinstance(index_val, str) and index_val.isdigit():
                    index_val = int(index_val)
                    param["index"] = index_val

                if not isinstance(index_val, int):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Index must be an integer, found: {index_val}",
                    )

                index_values.append(index_val)

            # Check for duplicate indices
            if len(index_values) != len(set(index_values)):
                duplicates = [x for x in index_values if index_values.count(x) > 1]
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate index values found: {set(duplicates)}",
                )

            notification_obj.params = params
            flag_modified(notification_obj, "params")

        notification_obj.label = notification.get("label", notification_obj.label)
        notification_obj.status = notification.get("status", notification_obj.status)
        notification_obj.color = notification.get("color", notification_obj.color)
        notification_obj.description = notification.get(
            "description", notification_obj.description
        )
        notification_obj.content = notification.get("content", notification_obj.content)

        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_notification(db: AsyncSession, notification_id: str) -> None:
    """
    Delete a notification from the database by its ID.
    """
    try:
        await notification_repository.delete_notification(db, notification_id)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_multiple_notifications(
    db: AsyncSession, notification_ids: list
) -> None:
    """
    Delete multiple notifications from the database by their IDs.
    """
    try:
        await notification_repository.delete_multiple_notifications(
            db, notification_ids
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def download_notifications_as_excel(db: AsyncSession) -> BytesIO:
    """
    Download all notifications as an Excel file stream (BytesIO).
    The Excel file will contain:
    1. 'data' sheet: Contains all notifications with sequential integer IDs
    2. 'n_{id}' sheets: One sheet per notification with its parameters

    Returns:
        BytesIO: Excel file contents in a BytesIO buffer.
    """
    try:
        # Get all notifications
        notifications = await notification_repository.get_all_notifications(db)
        if not notifications:
            return None
        data_list = []
        for idx, notification in enumerate(notifications, 1):  # Start from 1
            data_list.append(
                {
                    "id": idx,
                    "original_id": notification.id,  # Keep the original ID for reference
                    "label": notification.label,
                    "color": notification.color,
                    "status": notification.status,
                    "description": notification.description,
                    "content": notification.content,
                }
            )

        # Create DataFrame for the main 'data' sheet
        df_data = pd.DataFrame(data_list)
        excel_buffer = BytesIO()
        # Write to Excel file
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            # Write 'data' sheet
            # Only include visible columns (excluding original_id)
            visible_columns = [
                "id",
                "label",
                "color",
                "status",
                "description",
                "content",
            ]
            df_data[visible_columns].to_excel(writer, index=False, sheet_name="data")

            worksheet_data = writer.sheets["data"]
            for cell in worksheet_data[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")
            if not df_data.empty:
                adjust_column_widths_in_worksheet(
                    worksheet_data, df_data[visible_columns]
                )  # Create individual sheets for each notification's parameters
            for idx, notification in enumerate(notifications, 1):
                if notification.params:
                    sheet_name = f"n_{idx}"
                    # Create params DataFrame
                    params_data = []
                    if isinstance(notification.params, list):
                        for i, param in enumerate(notification.params):
                            # Ensure index is an integer - use param's index if available and valid, or use position+1
                            index_val = param.get("index")
                            if (
                                index_val is None
                                or not isinstance(index_val, (int, str))
                                or index_val == ""
                            ):
                                index_val = i + 1  # Start from 1
                            elif isinstance(index_val, str) and index_val.isdigit():
                                index_val = int(index_val)

                            params_data.append(
                                {
                                    "index": index_val,
                                    "param_name": param.get("param_name", ""),
                                    "param_type": param.get("param_type", ""),
                                    "description": param.get("description", ""),
                                    "validation": param.get("validation", ""),
                                }
                            )

                    if params_data:
                        df_params = pd.DataFrame(params_data)
                        df_params.to_excel(writer, index=False, sheet_name=sheet_name)

                        worksheet_params = writer.sheets[sheet_name]
                        for cell in worksheet_params[1]:  # Header row
                            cell.alignment = Alignment(horizontal="left")
                        if len(params_data) > 0:
                            adjust_column_widths_in_worksheet(
                                worksheet_params, df_params
                            )
                    else:
                        # Create empty sheet with headers
                        df_empty = pd.DataFrame(
                            columns=[
                                "index",
                                "param_name",
                                "param_type",
                                "description",
                                "validation",
                            ]
                        )
                        df_empty.to_excel(writer, index=False, sheet_name=sheet_name)

                        worksheet_empty = writer.sheets[sheet_name]
                        for cell in worksheet_empty[1]:  # Header row
                            cell.alignment = Alignment(horizontal="left")

        excel_buffer.seek(0)  # Reset to beginning of buffer
        return excel_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def upload_notifications_from_excel(
    db: AsyncSession, file_content: bytes
) -> None:
    """
    Upload notifications from an Excel file content.
    The Excel file should have:
    1. 'data' sheet: Contains notifications with id, label, color, status, description, content
    2. 'n_{id}' sheets: One sheet per notification with its parameters (index, param_name, param_type, description)
    """
    try:
        # Read all sheets from the Excel file content
        sheets_dict = pd.read_excel(
            BytesIO(file_content), sheet_name=None, engine="openpyxl"
        )

        # Check if 'data' sheet exists
        if "data" not in sheets_dict:
            raise HTTPException(status_code=400, detail="Missing 'data' sheet")

        # Process the 'data' sheet
        # Check for required columns in data sheet
        data_df = sheets_dict["data"]
        required_columns = ["id", "label", "color", "status", "description", "content"]
        for col in required_columns:
            if col not in data_df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required column '{col}' in data sheet",
                )

        # Validate ID values - must be integers and unique
        id_values = data_df["id"].tolist()

        # Check if all IDs are integers
        for id_val in id_values:
            if pd.isna(id_val) or not (
                isinstance(id_val, int)
                or (isinstance(id_val, float) and id_val.is_integer())
            ):
                raise HTTPException(
                    status_code=400, detail=f"ID must be an integer, found: {id_val}"
                )

        # Check for duplicate IDs
        if len(id_values) != len(set(id_values)):
            duplicates = [x for x in id_values if id_values.count(x) > 1]
            raise HTTPException(
                status_code=400, detail=f"Duplicate ID values found: {set(duplicates)}"
            )

        # Iterate through each notification in the data sheet
        for idx, row in data_df.iterrows():
            # Get notification ID from the row
            # Find corresponding parameters sheet (n_{id})
            id_value = int(row["id"])
            param_sheet_name = f"n_{id_value}"
            params = []
            # If parameter sheet exists, process it
            if param_sheet_name in sheets_dict:
                param_df = sheets_dict[param_sheet_name]

                # Check if the parameter sheet has the required columns
                param_columns = [
                    "index",
                    "param_name",
                    "param_type",
                    "description",
                    "validation",
                ]
                for col in param_columns:
                    if col not in param_df.columns:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Missing required column '{col}' in parameter sheet '{param_sheet_name}'",
                        )

                # Filter out rows where all values are NaN/None/empty
                valid_param_rows = []
                for _, param_row in param_df.iterrows():
                    if not all(
                        pd.isna(param_row[col]) or param_row[col] == ""
                        for col in param_columns
                    ):
                        valid_param_rows.append(param_row)

                # Check if index values are valid integers and not empty
                index_values = []
                for param_row in valid_param_rows:
                    index_val = param_row["index"]
                    if pd.isna(index_val):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Empty index value found in sheet '{param_sheet_name}'",
                        )

                    if not (
                        isinstance(index_val, int)
                        or (isinstance(index_val, float) and index_val.is_integer())
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Index must be an integer, found: {index_val} in sheet '{param_sheet_name}'",
                        )

                    index_values.append(int(index_val))

                # Check for duplicate index values
                if len(index_values) != len(set(index_values)):
                    duplicates = [x for x in index_values if index_values.count(x) > 1]
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate index values found in sheet '{param_sheet_name}': {set(duplicates)}",
                    )

                # Process each parameter in the sheet
                for param_row in valid_param_rows:
                    params.append(
                        {
                            "index": int(param_row["index"]),
                            "param_name": (
                                str(param_row["param_name"])
                                if not pd.isna(param_row["param_name"])
                                else ""
                            ),
                            "param_type": (
                                str(param_row["param_type"])
                                if not pd.isna(param_row["param_type"])
                                else ""
                            ),
                            "description": (
                                str(param_row["description"])
                                if not pd.isna(param_row["description"])
                                else ""
                            ),
                            "validation": (
                                str(param_row["validation"])
                                if not pd.isna(param_row["validation"])
                                else ""
                            ),
                        }
                    )

            # Create notification object
            notification = {
                "label": str(row["label"]) if not pd.isna(row["label"]) else "",
                "status": (
                    str(row["status"]) if not pd.isna(row["status"]) else "published"
                ),
                "color": str(row["color"]) if not pd.isna(row["color"]) else "#000000",
                "description": (
                    str(row["description"]) if not pd.isna(row["description"]) else ""
                ),
                "content": str(row["content"]) if not pd.isna(row["content"]) else "",
                "params": params,
            }

            # Insert notification to database
            await insert_notification(db, notification)

        return f"Successfully imported {len(data_df)} notifications"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_notification_template() -> BytesIO:
    """
    Generate a template Excel file for notifications.
    The template will contain:
    1. 'data' sheet with example columns
    2. 'n_1' sheet with example parameters

    Returns:
        str: Path to the template Excel file
    """
    try:
        # --- Prepare 'data' sheet with sample data ---
        data_list = [
            {
                "id": 1,
                "label": "Another Example",
                "color": "#e74c3c",
                "status": "draft",
                "description": "Example description for a second notification",
                "content": "Example content with {{ param1 }} and {{ param2 }}",
            },
            {
                "id": 2,
                "label": "Sample Notification",
                "color": "#3498db",
                "status": "published",
                "description": "This is a sample notification template",
                "content": "Sample content for notification",
            },
        ]
        df_data = pd.DataFrame(data_list)

        # --- Prepare 'n_1' sheet with sample parameters ---
        params_data = [
            {
                "index": 1,
                "param_name": "param1",
                "param_type": "string",
                "description": "First parameter example",
            },
            {
                "index": 2,
                "param_name": "param2",
                "param_type": "number",
                "description": "Second parameter example",
                "validation": "phone",
            },
        ]
        df_params = pd.DataFrame(params_data)
        excel_buffer = BytesIO()
        # Write to Excel file
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            # Write 'data' sheet
            df_data.to_excel(writer, index=False, sheet_name="data")
            worksheet_data = writer.sheets["data"]
            for cell in worksheet_data[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")
            adjust_column_widths_in_worksheet(worksheet_data, df_data)

            # Write 'n_1' sheet
            df_params.to_excel(writer, index=False, sheet_name="n_1")
            worksheet_params = writer.sheets["n_1"]
            for cell in worksheet_params[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")
            adjust_column_widths_in_worksheet(worksheet_params, df_params)

            # Write 'n_2' sheet (empty example with headers)
            df_empty = pd.DataFrame(
                columns=[
                    "index",
                    "param_name",
                    "param_type",
                    "description",
                    "validation",
                ]
            )
            df_empty.to_excel(writer, index=False, sheet_name="n_2")
            worksheet_empty = writer.sheets["n_2"]
            for cell in worksheet_empty[1]:  # Header row
                cell.alignment = Alignment(horizontal="left")

        excel_buffer.seek(0)  # Reset to beginning of buffer
        return excel_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
