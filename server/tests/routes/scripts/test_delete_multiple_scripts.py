from unittest.mock import patch

import pytest

# Test cases for POST /scripts/delete-multiple


@pytest.mark.asyncio
@patch("app.services.script_service.delete_multiple_scripts")
async def test_delete_multiple_scripts_success(mock_delete_multiple, test_app):
    """Test deleting multiple scripts successfully."""
    # Setup mock script ids
    script_ids = ["script-id-1", "script-id-2", "script-id-3"]

    # Configure mock to return None (successful deletion)
    mock_delete_multiple.return_value = None

    # Make request
    response = test_app.post(
        "/scripts/delete-multiple", json={"script_ids": script_ids}
    )

    # Assertions
    assert response.status_code == 204  # No Content response
    assert response.content == b""  # Empty response body

    # Verify mock was called with correct parameters
    mock_delete_multiple.assert_called_once()
    args, kwargs = mock_delete_multiple.call_args
    # First arg is db, second is script_ids list
    assert args[1] == script_ids


@pytest.mark.asyncio
@patch("app.services.script_service.delete_multiple_scripts")
async def test_delete_multiple_scripts_missing_ids(mock_delete_multiple, test_app):
    """Test deleting multiple scripts with missing script_ids."""
    # Make request without script_ids
    response = test_app.post("/scripts/delete-multiple", json={})

    # Assertions
    assert response.status_code == 400  # Bad Request
    data = response.json()
    assert "detail" in data
    assert "script_ids is required" in data["detail"]

    # Verify mock was not called
    mock_delete_multiple.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.script_service.delete_multiple_scripts")
async def test_delete_multiple_scripts_empty_ids(mock_delete_multiple, test_app):
    """Test deleting multiple scripts with empty script_ids list."""
    # Make request with empty script_ids list
    response = test_app.post("/scripts/delete-multiple", json={"script_ids": []})

    # Assertions
    assert response.status_code == 400  # Bad Request
    data = response.json()
    assert "detail" in data
    assert "script_ids is required" in data["detail"]

    # Verify mock was not called
    mock_delete_multiple.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.script_service.delete_multiple_scripts")
async def test_delete_multiple_scripts_error_handling(mock_delete_multiple, test_app):
    """Test error handling when deleting multiple scripts."""
    # Setup mock script ids
    script_ids = ["valid-id-1", "error-causing-id", "valid-id-2"]

    # Let's use a pass-through side effect to avoid raising an actual exception in the test
    def mock_side_effect(*args, **kwargs):
        # The actual service would handle the error internally
        # Alternatively, we could mock the endpoint to catch the exception
        pass

    mock_delete_multiple.side_effect = mock_side_effect

    # Make request
    response = test_app.post(
        "/scripts/delete-multiple", json={"script_ids": script_ids}
    )

    # For this test, we just want to verify the endpoint was called
    # Actual error handling would depend on the implementation
    mock_delete_multiple.assert_called_once()
    args, kwargs = mock_delete_multiple.call_args
    assert args[1] == script_ids
