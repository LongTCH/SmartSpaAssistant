from unittest.mock import patch

import pytest

# Test cases for GET /scripts/{script_id}


@pytest.mark.asyncio
@patch("app.services.script_service.get_script_by_id")
async def test_get_script_by_id_found(mock_get_script_by_id, test_app):
    """Test getting a script by ID when the script exists."""
    # Setup mock script
    script_id = "test-script-id"

    # Create a dictionary as the returned object
    mock_script = {
        "id": script_id,
        "name": "Test Script",
        "description": "Test Description",
        "solution": "Test Solution",
        "status": "published",
        "created_at": "2023-01-01T00:00:00",
    }

    # Configure mock to return the script dictionary
    mock_get_script_by_id.return_value = mock_script

    # Make request
    response = test_app.get(f"/scripts/{script_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == script_id
    assert data["name"] == mock_script["name"]
    assert data["description"] == mock_script["description"]
    assert data["solution"] == mock_script["solution"]
    assert data["status"] == mock_script["status"]

    # Verify mock was called with correct parameters
    mock_get_script_by_id.assert_called_once()
    args, kwargs = mock_get_script_by_id.call_args
    # First arg is db, second is script_id
    assert args[1] == script_id


@pytest.mark.asyncio
@patch("app.services.script_service.get_script_by_id")
async def test_get_script_by_id_not_found(mock_get_script_by_id, test_app):
    """Test getting a script by ID when the script does not exist."""
    # Setup mock to return None (script not found)
    script_id = "non-existent-script-id"
    mock_get_script_by_id.return_value = None

    # Make request
    response = test_app.get(f"/scripts/{script_id}")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Script not found" in data["detail"]

    # Verify mock was called with correct parameters
    mock_get_script_by_id.assert_called_once()
    args, kwargs = mock_get_script_by_id.call_args
    # First arg is db, second is script_id
    assert args[1] == script_id
