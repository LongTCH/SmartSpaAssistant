from unittest.mock import patch

import pytest
from app.dtos import PaginationDto

# Test cases for GET /scripts


@pytest.mark.asyncio
@patch("app.services.script_service.get_scripts")
async def test_get_scripts_all(mock_get_scripts, test_app):
    """Test getting all scripts."""
    # Create mock script data
    mock_scripts = [
        {
            "id": "script-1",
            "name": "Test Script 1",
            "description": "Test description 1",
            "solution": "Test solution 1",
            "status": "published",
            "created_at": "2023-01-01T00:00:00",
        },
        {
            "id": "script-2",
            "name": "Test Script 2",
            "description": "Test description 2",
            "solution": "Test solution 2",
            "status": "draft",
            "created_at": "2023-01-02T00:00:00",
        },
    ]

    # Setup mock
    mock_get_scripts.return_value = PaginationDto(
        page=1, limit=10, total=len(mock_scripts), data=mock_scripts
    )

    # Make request
    response = test_app.get("/scripts")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(mock_scripts)
    assert len(data["data"]) == len(mock_scripts)
    assert "page" in data
    assert "limit" in data
    assert "has_next" in data
    assert "has_prev" in data
    assert "total_pages" in data

    # Verify mock was called with correct parameters
    mock_get_scripts.assert_called_once()
    args, kwargs = mock_get_scripts.call_args
    # First arg is db, second is page, third is limit
    assert args[1] == 1  # page
    assert args[2] == 10  # limit


@pytest.mark.asyncio
@patch("app.services.script_service.get_scripts_by_status")
async def test_get_scripts_by_status(mock_get_scripts_by_status, test_app):
    """Test getting scripts filtered by status."""
    # Create mock script data with "published" status
    status = "published"
    mock_scripts = [
        {
            "id": "script-1",
            "name": "Test Script 1",
            "description": "Test description 1",
            "solution": "Test solution 1",
            "status": status,
            "created_at": "2023-01-01T00:00:00",
        },
        {
            "id": "script-3",
            "name": "Test Script 3",
            "description": "Test description 3",
            "solution": "Test solution 3",
            "status": status,
            "created_at": "2023-01-03T00:00:00",
        },
    ]

    mock_get_scripts_by_status.return_value = PaginationDto(
        page=1, limit=10, total=len(mock_scripts), data=mock_scripts
    )

    # Make request
    response = test_app.get(f"/scripts?status={status}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(mock_scripts)
    assert all(script["status"] == status for script in data["data"])

    # Verify mock was called with correct parameters
    mock_get_scripts_by_status.assert_called_once()
    args, kwargs = mock_get_scripts_by_status.call_args
    # First arg is db, second is page, third is limit, fourth is status
    assert args[1] == 1  # page
    assert args[2] == 10  # limit
    assert args[3] == status


@pytest.mark.asyncio
@patch("app.services.script_service.get_scripts")
async def test_get_scripts_pagination(mock_get_scripts, test_app):
    """Test pagination for getting scripts."""
    # Setup custom pagination parameters
    page = 2
    limit = 5

    # Create mock script data
    mock_scripts = [
        {
            "id": f"script-{i}",
            "name": f"Test Script {i}",
            "description": f"Test description {i}",
            "solution": f"Test solution {i}",
            "status": "published" if i % 2 == 0 else "draft",
            "created_at": f"2023-01-{i:02d}T00:00:00",
        }
        for i in range(1, 11)  # Total of 10 scripts
    ]

    # Mock should return scripts 6-10 for page 2, limit 5
    page_data = mock_scripts[5:10]
    mock_get_scripts.return_value = PaginationDto(
        page=page,
        limit=limit,
        total=len(mock_scripts),
        data=page_data,
    )

    # Make request
    response = test_app.get(f"/scripts?page={page}&limit={limit}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == page
    assert data["limit"] == limit
    assert len(data["data"]) == len(page_data)
    assert data["total"] == len(mock_scripts)
    assert data["total_pages"] == (len(mock_scripts) + limit - 1) // limit

    # Verify mock was called with correct parameters
    mock_get_scripts.assert_called_once()
    args, kwargs = mock_get_scripts.call_args
    # First arg is db, second is page, third is limit
    assert args[1] == page
    assert args[2] == limit
