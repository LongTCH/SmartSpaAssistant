from unittest.mock import patch

import pytest
from app.configs.constants import CHAT_ASSIGNMENT
from app.dtos import PagingDto

# Test cases for GET /conversations


@pytest.mark.asyncio
@patch("app.services.guest_service.get_conversations")
async def test_get_conversations_all(mock_get_conversations, mock_guest_list, test_app):
    """Test getting all conversations."""
    # Setup mock
    mock_get_conversations.return_value = PagingDto(
        skip=0, limit=10, data=mock_guest_list, total=len(mock_guest_list)
    )

    # Make request
    response = test_app.get("/conversations")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(mock_guest_list)
    assert len(data["data"]) == len(mock_guest_list)
    assert "skip" in data
    assert "limit" in data
    assert "has_next" in data
    assert "has_prev" in data

    # Verify mock was called with correct parameters
    mock_get_conversations.assert_called_once()
    args, kwargs = mock_get_conversations.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là skip, thứ ba là limit
    assert args[1] == 0  # skip
    assert args[2] == 10  # limit


@pytest.mark.asyncio
@patch("app.services.guest_service.get_conversations_by_assignment")
async def test_get_conversations_by_assignment(
    mock_get_conversations_by_assignment, mock_guest_list, test_app
):
    """Test getting conversations filtered by assignment."""
    # Setup mock - Filter to just AI assigned conversations
    filtered_guests = [
        g for g in mock_guest_list if g.assigned_to == CHAT_ASSIGNMENT.AI.value
    ]
    mock_get_conversations_by_assignment.return_value = PagingDto(
        skip=0, limit=10, data=filtered_guests, total=len(filtered_guests)
    )

    # Make request
    response = test_app.get(f"/conversations?assigned_to={CHAT_ASSIGNMENT.AI.value}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(filtered_guests)
    assert all(
        guest["assigned_to"] == CHAT_ASSIGNMENT.AI.value for guest in data["data"]
    )

    # Verify mock was called with correct parameters
    mock_get_conversations_by_assignment.assert_called_once()
    args, kwargs = mock_get_conversations_by_assignment.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là assigned_to, thứ ba là skip, thứ tư là limit
    assert args[1] == CHAT_ASSIGNMENT.AI.value  # assigned_to
    assert args[2] == 0  # skip
    assert args[3] == 10  # limit


@pytest.mark.asyncio
@patch("app.services.guest_service.get_conversations")
async def test_get_conversations_pagination(
    mock_get_conversations, mock_guest_list, test_app
):
    """Test pagination for getting conversations."""
    # Setup custom pagination parameters
    skip = 1
    limit = 2

    mock_get_conversations.return_value = PagingDto(
        skip=skip,
        limit=limit,
        data=mock_guest_list[skip : skip + limit],
        total=len(mock_guest_list),
    )

    # Make request
    response = test_app.get(f"/conversations?skip={skip}&limit={limit}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == skip
    assert data["limit"] == limit
    assert len(data["data"]) == len(mock_guest_list[skip : skip + limit])

    # Verify mock was called with correct parameters
    mock_get_conversations.assert_called_once()
    args, kwargs = mock_get_conversations.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là skip, thứ ba là limit
    assert args[1] == skip  # skip
    assert args[2] == limit  # limit
