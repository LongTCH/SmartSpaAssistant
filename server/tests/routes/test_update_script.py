from unittest.mock import MagicMock, patch

import pytest

# Test cases for PUT /scripts/{script_id}


@pytest.mark.asyncio
@patch("app.services.script_service.update_script")
@patch("app.services.script_service.get_script_by_id")
async def test_update_script_success(
    mock_get_script_by_id, mock_update_script, test_app
):
    """Test updating an existing script successfully."""
    # Setup mock script id and data
    script_id = "existing-script-id"

    # Original script as object (not dictionary) to match route behavior
    original_script = MagicMock()
    original_script.id = script_id
    original_script.name = "Original Script Name"
    original_script.description = "Original Description"
    original_script.solution = "Original Solution"
    original_script.status = "draft"
    original_script.created_at = "2023-01-01T12:00:00"

    # Update data
    update_data = {
        "name": "Updated Script Name",
        "description": "Updated Description",
        "solution": "Updated Solution",
        "status": "published",
    }

    # Updated script data (after applying updates)
    updated_script = {
        "id": script_id,
        "name": update_data["name"],
        "description": update_data["description"],
        "solution": update_data["solution"],
        "status": update_data["status"],
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mocks
    mock_get_script_by_id.return_value = original_script
    mock_update_script.return_value = updated_script

    # Make request
    response = test_app.put(f"/scripts/{script_id}", json=update_data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == script_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["solution"] == update_data["solution"]
    assert data["status"] == update_data["status"]

    # Verify mock_get_script_by_id was called with correct parameters
    mock_get_script_by_id.assert_called_once()
    args, kwargs = mock_get_script_by_id.call_args
    assert args[1] == script_id  # First arg is db, second is script_id


@pytest.mark.asyncio
@patch("app.services.script_service.get_script_by_id")
async def test_update_script_not_found(mock_get_script_by_id, test_app):
    """Test updating a script that doesn't exist."""
    # Setup mock
    script_id = "non-existent-script-id"
    mock_get_script_by_id.return_value = None

    # Update data
    update_data = {
        "name": "Updated Script Name",
        "description": "Updated Description",
        "solution": "Updated Solution",
        "status": "published",
    }

    # Make request
    response = test_app.put(f"/scripts/{script_id}", json=update_data)

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Script not found" in data["detail"]

    # Verify mock was called with correct parameters
    mock_get_script_by_id.assert_called_once()
    args, kwargs = mock_get_script_by_id.call_args
    assert args[1] == script_id  # First arg is db, second is script_id


@pytest.mark.asyncio
@patch("app.services.script_service.update_script")
@patch("app.services.script_service.get_script_by_id")
async def test_update_script_partial(
    mock_get_script_by_id, mock_update_script, test_app
):
    """Test partially updating a script (only some fields)."""
    # Setup mock script id and data
    script_id = "existing-script-id"

    # Original script as object (not dictionary) to match route behavior
    original_script = MagicMock()
    original_script.id = script_id
    original_script.name = "Original Script Name"
    original_script.description = "Original Description"
    original_script.solution = "Original Solution"
    original_script.status = "draft"
    original_script.created_at = "2023-01-01T12:00:00"

    # Partial update data (only name and status)
    update_data = {
        "name": "Updated Script Name",
        "status": "published",
    }

    # Expected updated script data
    updated_script = {
        "id": script_id,
        "name": update_data["name"],
        "description": original_script.description,  # Unchanged
        "solution": original_script.solution,  # Unchanged
        "status": update_data["status"],
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mocks
    mock_get_script_by_id.return_value = original_script
    mock_update_script.return_value = updated_script

    # Make request
    response = test_app.put(f"/scripts/{script_id}", json=update_data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == script_id
    assert data["name"] == update_data["name"]  # Updated
    assert data["description"] == original_script.description  # Unchanged
    assert data["solution"] == original_script.solution  # Unchanged
    assert data["status"] == update_data["status"]  # Updated
