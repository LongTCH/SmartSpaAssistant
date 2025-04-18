from unittest.mock import patch

import pytest

# Test cases for POST /scripts


@pytest.mark.asyncio
@patch("app.services.script_service.insert_script")
async def test_create_script_success(mock_insert_script, test_app):
    """Test creating a new script successfully."""
    # Setup mock script data
    script_data = {
        "name": "New Test Script",
        "description": "New Test Description",
        "solution": "New Test Solution",
        "status": "draft",
    }

    # Create a dictionary as the returned object
    returned_script = {
        "id": "new-script-id",
        "name": script_data["name"],
        "description": script_data["description"],
        "solution": script_data["solution"],
        "status": script_data["status"],
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mock to return the script dictionary
    mock_insert_script.return_value = returned_script

    # Make request
    response = test_app.post("/scripts", json=script_data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == returned_script["id"]
    assert data["name"] == script_data["name"]
    assert data["description"] == script_data["description"]
    assert data["solution"] == script_data["solution"]
    assert data["status"] == script_data["status"]
    assert "created_at" in data

    # Verify mock was called with correct parameters
    mock_insert_script.assert_called_once()
    args, kwargs = mock_insert_script.call_args
    # First arg is db, second is script_data
    assert args[1] == script_data


@pytest.mark.asyncio
@patch("app.services.script_service.insert_script")
async def test_create_script_with_default_status(mock_insert_script, test_app):
    """Test creating a new script with default 'published' status."""
    # Setup mock script data without status (should default to 'published')
    script_data = {
        "name": "New Test Script",
        "description": "New Test Description",
        "solution": "New Test Solution",
    }

    # Create a dictionary as the returned object with default status
    returned_script = {
        "id": "new-script-id",
        "name": script_data["name"],
        "description": script_data["description"],
        "solution": script_data["solution"],
        "status": "published",  # Default status
        "created_at": "2023-01-01T12:00:00",
    }

    # Configure mock to return the script dictionary
    mock_insert_script.return_value = returned_script

    # Make request
    response = test_app.post("/scripts", json=script_data)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"  # Check for default status

    # Verify mock was called correctly
    mock_insert_script.assert_called_once()
    args, kwargs = mock_insert_script.call_args
    # The service should have received the data without the status,
    # and the model's default value should be used
    assert args[1] == script_data
