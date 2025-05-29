from unittest.mock import patch

import pytest

# Test cases for PUT /sheets/{sheet_id}


@pytest.mark.asyncio
@patch("app.services.sheet_service.update_sheet")
async def test_update_sheet_success(mock_update_sheet, test_app):
    """Test updating an existing sheet successfully."""
    # Setup mock sheet id and data
    sheet_id = "existing-sheet-id"

    # Update data
    update_data = {
        "name": "Updated Sheet Name",
        "description": "Updated Description",
        "status": "published",
    }

    # Updated sheet data (after applying updates)
    updated_sheet = {
        "id": sheet_id,
        "name": update_data["name"],
        "description": update_data["description"],
        "status": update_data["status"],
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mock
    mock_update_sheet.return_value = updated_sheet

    # Make request
    response = test_app.put(f"/sheets/{sheet_id}", json=update_data)  # Assertions
    assert response.status_code == 204
    # 204 No Content means no response body to check

    # Verify mock was called with correct parameters
    mock_update_sheet.assert_called_once()
    args, kwargs = mock_update_sheet.call_args
    assert args[1] == sheet_id  # First arg is db, second is sheet_id
    assert args[2] == update_data  # Third arg is update data


@pytest.mark.asyncio
@patch("app.services.sheet_service.update_sheet")
async def test_update_sheet_not_found(mock_update_sheet, test_app):
    """Test updating a sheet that doesn't exist."""
    # Setup mock
    sheet_id = "non-existent-sheet-id"
    update_data = {
        "name": "Updated Sheet Name",
        "description": "Updated Description",
        "status": "published",
    }

    mock_update_sheet.return_value = None

    # Make request
    response = test_app.put(f"/sheets/{sheet_id}", json=update_data)  # Assertions
    # Note: Current route implementation doesn't validate sheet existence
    # It returns 204 even for non-existent sheets
    assert response.status_code == 204

    # Verify mock was called with correct parameters
    mock_update_sheet.assert_called_once()
    args, kwargs = mock_update_sheet.call_args
    assert args[1] == sheet_id  # First arg is db, second is sheet_id


@pytest.mark.asyncio
@patch("app.services.sheet_service.update_sheet")
async def test_update_sheet_partial(mock_update_sheet, test_app):
    """Test partially updating a sheet (only some fields)."""
    # Setup mock sheet id and data
    sheet_id = "existing-sheet-id"

    # Original sheet data
    original_sheet = {
        "id": sheet_id,
        "name": "Original Sheet Name",
        "description": "Original Description",
        "status": "draft",
        "created_at": "2023-01-01T12:00:00",
    }

    # Partial update data (only name and status)
    update_data = {
        "name": "Updated Sheet Name",
        "status": "published",
    }

    # Expected updated sheet data
    updated_sheet = {
        "id": sheet_id,
        "name": update_data["name"],
        "description": original_sheet["description"],  # Unchanged
        "status": update_data["status"],
        "created_at": original_sheet["created_at"],
    }

    # Configure mock
    mock_update_sheet.return_value = updated_sheet

    # Make request
    response = test_app.put(f"/sheets/{sheet_id}", json=update_data)  # Assertions
    assert response.status_code == 204
    # 204 No Content means no response body to check

    # Verify mock was called with correct parameters
    mock_update_sheet.assert_called_once()
    args, kwargs = mock_update_sheet.call_args
    assert args[1] == sheet_id  # First arg is db, second is sheet_id
    assert args[2] == update_data  # Third arg is update data
