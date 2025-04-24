from unittest.mock import patch

import pytest
from app.configs.constants import CHAT_ASSIGNMENT

# Test cases for PATCH /conversations/{guest_id}/assignment


@pytest.mark.asyncio
@patch("app.services.guest_service.update_assignment")
async def test_update_assignment_success(mock_update_assignment, mock_guest, test_app):
    """Test successfully updating a conversation's assignment."""
    # Setup mock
    guest_id = "test-guest-id"
    new_assignment = CHAT_ASSIGNMENT.ME.value

    # Update the dictionary to reflect new assignment
    mock_guest_updated = mock_guest.copy()
    mock_guest_updated["assigned_to"] = new_assignment
    mock_update_assignment.return_value = mock_guest_updated

    # Make request
    response = test_app.patch(
        f"/conversations/{guest_id}/assignment", json={"assigned_to": new_assignment}
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == guest_id
    assert data["assigned_to"] == new_assignment

    # Verify mock was called with correct parameters
    mock_update_assignment.assert_called_once()
    args, kwargs = mock_update_assignment.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là guest_id, thứ ba là assigned_to
    assert args[1] == guest_id  # guest_id
    assert args[2] == new_assignment  # assigned_to


@pytest.mark.asyncio
@patch("app.services.guest_service.update_assignment")
async def test_update_assignment_missing_param(mock_update_assignment, test_app):
    """Test updating a conversation with missing assignment parameter."""
    # Make request without assigned_to in body
    response = test_app.patch("/conversations/test-guest-id/assignment", json={})

    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "assigned_to is required" in data["detail"]

    # Verify mock was not called
    mock_update_assignment.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.guest_service.update_assignment")
async def test_update_assignment_guest_not_found(mock_update_assignment, test_app):
    """Test updating a conversation for a non-existent guest."""
    # Setup mock
    guest_id = "non-existent-guest-id"
    new_assignment = CHAT_ASSIGNMENT.ME.value
    mock_update_assignment.return_value = None  # Guest not found

    # Make request
    response = test_app.patch(
        f"/conversations/{guest_id}/assignment", json={"assigned_to": new_assignment}
    )

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Guest not found" in data["detail"]

    # Verify mock was called with correct parameters
    mock_update_assignment.assert_called_once()
    args, kwargs = mock_update_assignment.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là guest_id, thứ ba là assigned_to
    assert args[1] == guest_id  # guest_id
    assert args[2] == new_assignment  # assigned_to
