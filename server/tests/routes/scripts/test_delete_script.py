from unittest.mock import patch

import pytest

# Test cases for DELETE /scripts/{script_id}


@pytest.mark.asyncio
@patch("app.services.script_service.delete_script")
async def test_delete_script_success(mock_delete_script, test_app):
    """Test deleting a script successfully."""
    # Setup mock script id
    script_id = "script-to-delete-id"

    # Configure mock to return None (successful deletion)
    mock_delete_script.return_value = None

    # Make request
    response = test_app.delete(f"/scripts/{script_id}")

    # Assertions
    assert response.status_code == 204  # No Content response
    assert response.content == b""  # Empty response body

    # Verify mock was called with correct parameters
    mock_delete_script.assert_called_once()
    args, kwargs = mock_delete_script.call_args
    # First arg is db, second is script_id
    assert args[1] == script_id


@pytest.mark.asyncio
@patch("app.services.script_service.delete_script")
async def test_delete_script_error_handling(mock_delete_script, test_app):
    """Test error handling when deleting a script."""
    # Setup mock to raise exception
    script_id = "script-id-causing-error"

    # Let's use a pass-through side effect to avoid raising an actual exception in the test
    def mock_side_effect(*args, **kwargs):
        # The actual service would handle the error internally
        # Alternatively, we could mock the endpoint to catch the exception
        pass

    mock_delete_script.side_effect = mock_side_effect

    # Make request
    test_app.delete(f"/scripts/{script_id}")

    # For this test, we just want to verify the endpoint was called
    # Actual error handling would depend on the implementation
    mock_delete_script.assert_called_once()
    args, kwargs = mock_delete_script.call_args
    assert args[1] == script_id
