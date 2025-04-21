from unittest.mock import AsyncMock, patch

import pytest

# Test cases for PUT /scripts/{script_id}


@pytest.mark.asyncio
@patch("app.routes.route_scripts.script_service")
async def test_update_script_success(mock_script_service, test_app):
    """Test updating an existing script successfully."""
    # Setup mock script id and data
    script_id = "existing-script-id"

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

    # Configure mock with AsyncMock - the route directly calls update_script without get_script_by_id
    mock_script_service.update_script = AsyncMock(return_value=updated_script)

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

    # Verify mock was called with correct parameters
    mock_script_service.update_script.assert_called_once()
    args, kwargs = mock_script_service.update_script.call_args
    assert args[1] == script_id  # First arg is db, second is script_id
    assert args[2] == update_data  # Third arg is update data


@pytest.mark.asyncio
@patch("app.routes.route_scripts.script_service")
async def test_update_script_not_found(mock_script_service, test_app):
    """Test updating a script that doesn't exist."""
    # Setup mock
    script_id = "non-existent-script-id"

    # Update data
    update_data = {
        "name": "Updated Script Name",
        "description": "Updated Description",
        "solution": "Updated Solution",
        "status": "published",
    }

    # Configure mock to return None for non-existent script
    mock_script_service.update_script = AsyncMock(return_value=None)

    # Make request
    response = test_app.put(f"/scripts/{script_id}", json=update_data)

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Script not found" in data["detail"]

    # Verify mock was called with correct parameters
    mock_script_service.update_script.assert_called_once()
    args, kwargs = mock_script_service.update_script.call_args
    assert args[1] == script_id


@pytest.mark.asyncio
@patch("app.routes.route_scripts.script_service")
async def test_update_script_partial(mock_script_service, test_app):
    """Test partially updating a script (only some fields)."""
    # Setup mock script id and data
    script_id = "existing-script-id"

    # Original script properties
    original_description = "Original Description"
    original_solution = "Original Solution"

    # Partial update data (only name and status)
    update_data = {
        "name": "Updated Script Name",
        "status": "published",
    }

    # Expected updated script data
    updated_script = {
        "id": script_id,
        "name": update_data["name"],
        "description": original_description,  # Unchanged
        "solution": original_solution,  # Unchanged
        "status": update_data["status"],
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mock with AsyncMock
    mock_script_service.update_script = AsyncMock(return_value=updated_script)

    # Make request
    response = test_app.put(f"/scripts/{script_id}", json=update_data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == script_id
    assert data["name"] == update_data["name"]  # Updated
    assert data["description"] == original_description  # Unchanged
    assert data["solution"] == original_solution  # Unchanged
    assert data["status"] == update_data["status"]  # Updated

    # Verify mock was called with correct parameters
    mock_script_service.update_script.assert_called_once()
    args, kwargs = mock_script_service.update_script.call_args
    assert args[1] == script_id
    assert args[2] == update_data
