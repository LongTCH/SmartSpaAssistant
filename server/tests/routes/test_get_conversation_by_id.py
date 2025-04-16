from unittest.mock import patch

import pytest
from app.dtos import PagingDto

# Test cases for GET /conversations/{guest_id}


@pytest.mark.asyncio
@patch("app.services.guest_service.get_chat_by_guest_id")
async def test_get_conversation_by_guest_id(
    mock_get_chat_by_guest_id, mock_chat_list, test_app
):
    """Test getting a conversation by guest ID."""
    # Setup mock
    guest_id = "test-guest-id"
    mock_get_chat_by_guest_id.return_value = PagingDto(
        skip=0, limit=10, data=mock_chat_list, total=len(mock_chat_list)
    )

    # Make request
    response = test_app.get(f"/conversations/{guest_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(mock_chat_list)
    assert len(data["data"]) == len(mock_chat_list)
    assert all(chat["guest_id"] == guest_id for chat in data["data"])

    # Verify mock was called with correct parameters
    mock_get_chat_by_guest_id.assert_called_once()
    args, kwargs = mock_get_chat_by_guest_id.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là guest_id, thứ ba là skip, thứ tư là limit
    assert args[1] == guest_id  # guest_id
    assert args[2] == 0  # skip
    assert args[3] == 10  # limit


@pytest.mark.asyncio
@patch("app.services.guest_service.get_chat_by_guest_id")
async def test_get_conversation_by_guest_id_pagination(
    mock_get_chat_by_guest_id, mock_chat_list, test_app
):
    """Test pagination for getting a conversation by guest ID."""
    # Setup custom pagination parameters
    guest_id = "test-guest-id"
    skip = 1
    limit = 2

    mock_get_chat_by_guest_id.return_value = PagingDto(
        skip=skip,
        limit=limit,
        data=mock_chat_list[skip : skip + limit],
        total=len(mock_chat_list),
    )

    # Make request
    response = test_app.get(f"/conversations/{guest_id}?skip={skip}&limit={limit}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == skip
    assert data["limit"] == limit
    assert len(data["data"]) == len(mock_chat_list[skip : skip + limit])

    # Verify mock was called with correct parameters
    mock_get_chat_by_guest_id.assert_called_once()
    args, kwargs = mock_get_chat_by_guest_id.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là guest_id, thứ ba là skip, thứ tư là limit
    assert args[1] == guest_id  # guest_id
    assert args[2] == skip  # skip
    assert args[3] == limit  # limit


@pytest.mark.asyncio
@patch("app.services.guest_service.get_chat_by_guest_id")
async def test_get_conversation_empty_result(mock_get_chat_by_guest_id, test_app):
    """Test getting a conversation with no chat messages."""
    # Setup mock
    guest_id = "test-guest-id-no-chats"
    mock_get_chat_by_guest_id.return_value = PagingDto(
        skip=0, limit=10, data=[], total=0
    )

    # Make request
    response = test_app.get(f"/conversations/{guest_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["data"]) == 0
    assert data["has_next"] == False

    # Verify mock was called with correct parameters
    mock_get_chat_by_guest_id.assert_called_once()
    args, kwargs = mock_get_chat_by_guest_id.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là guest_id, thứ ba là skip, thứ tư là limit
    assert args[1] == guest_id  # guest_id
    assert args[2] == 0  # skip
    assert args[3] == 10  # limit
