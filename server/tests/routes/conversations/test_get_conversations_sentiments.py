from unittest.mock import patch

import pytest
from app.configs.constants import SENTIMENTS
from app.dtos import PagingDto

# Test cases for GET /conversations/sentiments


@pytest.mark.asyncio
@patch("app.services.guest_service.get_paging_guests_by_sentiment")
async def test_get_conversations_by_sentiment(
    mock_get_paging_guests_by_sentiment, mock_guest_list, test_app
):
    """Test getting conversations filtered by sentiment."""
    # Setup mock - Filter to just positive sentiment
    sentiment = SENTIMENTS.POSITIVE.value
    filtered_guests = [g for g in mock_guest_list if g["sentiment"] == sentiment]
    mock_get_paging_guests_by_sentiment.return_value = PagingDto(
        skip=0, limit=10, data=filtered_guests, total=len(filtered_guests)
    )

    # Make request
    response = test_app.get(f"/conversations/sentiments?sentiment={sentiment}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(filtered_guests)
    assert all(guest["sentiment"] == sentiment for guest in data["data"])

    # Verify mock was called with correct parameters
    mock_get_paging_guests_by_sentiment.assert_called_once()
    args, kwargs = mock_get_paging_guests_by_sentiment.call_args
    # Các tham số được truyền vào như positional args
    # Đầu tiên là db, thứ hai là sentiment, thứ ba là skip, thứ tư là limit
    assert args[1] == sentiment  # sentiment
    assert args[2] == 0  # skip
    assert args[3] == 10  # limit


@pytest.mark.asyncio
@patch("app.services.guest_service.get_paging_guests_by_sentiment")
async def test_get_conversations_by_invalid_sentiment(
    mock_get_paging_guests_by_sentiment, test_app
):
    """Test getting conversations with invalid sentiment parameter."""
    # Make request with invalid sentiment
    response = test_app.get("/conversations/sentiments?sentiment=invalid_sentiment")

    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid sentiment value" in data["detail"]

    # Verify mock was not called
    mock_get_paging_guests_by_sentiment.assert_not_called()
