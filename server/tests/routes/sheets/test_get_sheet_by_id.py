from unittest.mock import patch

import pytest

# Test cases for GET /sheets/{sheet_id}


@pytest.mark.asyncio
@patch("app.services.sheet_service.get_sheet_by_id")
async def test_get_sheet_by_id_success(mock_get_sheet_by_id, test_app):
    """Test getting a sheet by its ID successfully."""
    # Setup mock sheet data
    sheet_id = "existing-sheet-id"
    sheet_data = {
        "id": sheet_id,
        "name": "Test Sheet",
        "description": "Test Description",
        "status": "published",
        "created_at": "2023-01-01T12:00:00",
    }

    # Setup mock
    mock_get_sheet_by_id.return_value = sheet_data

    # Make request
    response = test_app.get(f"/sheets/{sheet_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sheet_id
    assert data["name"] == sheet_data["name"]
    assert data["description"] == sheet_data["description"]
    assert data["status"] == sheet_data["status"]
    assert data["created_at"] == sheet_data["created_at"]

    # Verify mock was called with correct parameters
    mock_get_sheet_by_id.assert_called_once()
    args, kwargs = mock_get_sheet_by_id.call_args
    # First arg is db, second is sheet_id
    assert args[1] == sheet_id


@pytest.mark.asyncio
@patch("app.services.sheet_service.get_sheet_by_id")
async def test_get_sheet_by_id_not_found(mock_get_sheet_by_id, test_app):
    """Test getting a sheet by ID that doesn't exist."""
    # Setup mock
    sheet_id = "non-existent-sheet-id"
    mock_get_sheet_by_id.return_value = None

    # Make request
    response = test_app.get(f"/sheets/{sheet_id}")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Sheet not found" in data["detail"]

    # Verify mock was called with correct parameters
    mock_get_sheet_by_id.assert_called_once()
    args, kwargs = mock_get_sheet_by_id.call_args
    # First arg is db, second is sheet_id
    assert args[1] == sheet_id
