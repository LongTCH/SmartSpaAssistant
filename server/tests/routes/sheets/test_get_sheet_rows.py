from unittest.mock import patch

import pytest
from app.dtos import PaginationDto

# Test cases for GET /sheets/{sheet_id}/rows


@pytest.mark.asyncio
@patch("app.services.sheet_service.get_sheet_rows_by_sheet_id")
async def test_get_sheet_rows_default_pagination(mock_get_sheet_rows, test_app):
    """Test getting sheet rows with default pagination parameters."""
    # Setup
    sheet_id = "test-sheet-id"

    # Create mock sheet rows data
    mock_rows = [
        {"id": f"row-{i}", "sheet_id": sheet_id, "data": f"Data {i}", "row_number": i}
        for i in range(1, 11)  # 10 rows
    ]

    # Setup mock response - using page for PaginationDto but the API uses skip
    mock_get_sheet_rows.return_value = PaginationDto(
        page=1, limit=10, total=len(mock_rows), data=mock_rows
    )

    # Make request with default pagination (skip=0, limit=10)
    response = test_app.get(f"/sheets/{sheet_id}/rows")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(mock_rows)
    assert len(data["data"]) == len(mock_rows)
    assert "page" in data
    assert "limit" in data

    # Verify mock was called with correct parameters
    mock_get_sheet_rows.assert_called_once()
    args, kwargs = mock_get_sheet_rows.call_args
    assert args[1] == sheet_id  # First arg is db, second is sheet_id
    assert args[2] == 0  # Third arg is skip (default 0)
    assert args[3] == 10  # Fourth arg is limit (default 10)


@pytest.mark.asyncio
@patch("app.services.sheet_service.get_sheet_rows_by_sheet_id")
async def test_get_sheet_rows_custom_pagination(mock_get_sheet_rows, test_app):
    """Test getting sheet rows with custom pagination parameters."""
    # Setup
    sheet_id = "test-sheet-id"
    skip = 5
    limit = 3

    # Create mock sheet rows data (total of 20 rows)
    all_rows = [
        {"id": f"row-{i}", "sheet_id": sheet_id, "data": f"Data {i}", "row_number": i}
        for i in range(1, 21)
    ]

    # Get the expected paginated subset (rows for skip=5, limit=3)
    paginated_rows = all_rows[skip : skip + limit]

    # Setup mock response - using page for PaginationDto but the API uses skip
    # For the PaginationDto, we convert skip to page
    page = (skip // limit) + 1
    mock_get_sheet_rows.return_value = PaginationDto(
        page=page, limit=limit, total=len(all_rows), data=paginated_rows
    )

    # Make request with custom pagination using skip and limit
    response = test_app.get(f"/sheets/{sheet_id}/rows?skip={skip}&limit={limit}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(all_rows)  # Total should be all rows
    # But data should be paginated
    assert len(data["data"]) == len(paginated_rows)

    # Verify mock was called with correct parameters
    mock_get_sheet_rows.assert_called_once()
    args, kwargs = mock_get_sheet_rows.call_args
    assert args[1] == sheet_id  # First arg is db, second is sheet_id
    assert args[2] == skip  # Third arg is skip
    assert args[3] == limit  # Fourth arg is limit


@pytest.mark.asyncio
@patch("app.services.sheet_service.get_sheet_rows_by_sheet_id")
async def test_get_sheet_rows_empty_result(mock_get_sheet_rows, test_app):
    """Test getting sheet rows when there are no rows."""
    # Setup
    sheet_id = "empty-sheet-id"

    # Setup mock to return empty data - using page for PaginationDto but the API uses skip
    mock_get_sheet_rows.return_value = PaginationDto(page=1, limit=10, total=0, data=[])

    # Make request
    response = test_app.get(f"/sheets/{sheet_id}/rows")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["data"]) == 0

    # Verify mock was called with correct parameters
    mock_get_sheet_rows.assert_called_once()
    args, kwargs = mock_get_sheet_rows.call_args
    assert args[1] == sheet_id
