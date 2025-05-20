# Import mock configurations first
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.configs.constants import CHAT_ASSIGNMENT
from app.models import Chat
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create mock for qdrant_client before any imports can occur
mock_qdrant = MagicMock()
mock_qdrant.collection_exists.return_value = True
mock_qdrant.search.return_value = []
mock_qdrant.http = MagicMock()
mock_qdrant.models = MagicMock()

# Create a fake module to inject


class MockQdrant:
    def __init__(self):
        self.qdrant_client = mock_qdrant


# Insert our mock into sys.modules to intercept all imports
sys.modules["app.configs.qdrant"] = MockQdrant()

# Now we can safely import the rest

# Create a mock DB session


@pytest.fixture
def mock_db_session():
    """Fixture for mocked database session"""
    db = AsyncMock(spec=AsyncSession)
    db.commit.return_value = None
    db.rollback.return_value = None
    db.close.return_value = None
    return db


# Override the get_session dependency


@pytest.fixture
def override_get_session(mock_db_session):
    """Override the get_session dependency"""
    from app.configs.database import get_session
    from app.main import app

    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_session] = _get_db_override

    yield

    # Reset the override after the test
    app.dependency_overrides = {}


# Mock FastAPI test client for the app with DB dependency overridden


@pytest.fixture
def test_app(override_get_session):
    from app.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)


# Apply additional mocks for dependencies we need to control


@pytest.fixture(autouse=True, scope="session")
def mock_external_dependencies():
    # Create patches for all other external dependencies
    patches = [
        # Mock database connections
        patch(
            "app.configs.database.init_models",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.configs.database.shutdown_models",
            new_callable=AsyncMock,
            return_value=None,
        ),
        # Mock Google services if used
        patch(
            "app.services.integrations.google_service.get_service",
            return_value=MagicMock(),
            create=True,
        ),
    ]

    # Start all patches
    mocks = [p.start() for p in patches]

    yield mocks

    # Stop all patches when done
    for p in patches:
        p.stop()


# Add fixtures for mock objects


@pytest.fixture
def mock_guest():
    """Create a mock Guest dictionary for testing."""
    guest_info_dict = {
        "id": "test-guest-info-id",
        "fullname": "Test User",
        "gender": "male",
        "birthday": datetime(1990, 1, 1).isoformat(),
        "phone": "0123456789",
        "email": "test@example.com",
        "address": "123 Test Street",
    }

    guest_dict = {
        "id": "test-guest-id",
        "provider": "messenger",
        "account_id": "12345678",
        "account_name": "test_user",
        "avatar": "http://example.com/avatar.jpg",
        "last_message_at": datetime.now().isoformat(),
        "last_message": {"text": "Hello world"},
        "assigned_to": CHAT_ASSIGNMENT.AI.value,
        "info": guest_info_dict,
        "info_id": guest_info_dict["id"],
    }

    return guest_dict


@pytest.fixture
def mock_chat():
    """Create a mock Chat object for testing."""
    chat = Chat(
        id="test-chat-id",
        guest_id="test-guest-id",
        content={"side": "client", "message": {"text": "Hello"}},
        created_at=datetime.now(),
    )
    return chat


@pytest.fixture
def mock_guest_list():
    """Create a list of mock Guest dictionaries for testing."""
    guests = []
    for i in range(3):
        guest_info_dict = {
            "id": f"test-guest-info-id-{i}",
            "fullname": f"Test User {i}",
            "gender": "male" if i % 2 == 0 else "female",
            "birthday": datetime(1990, 1, 1).isoformat(),
            "phone": f"012345678{i}",
            "email": f"test{i}@example.com",
            "address": f"123 Test Street {i}",
        }

        guest_dict = {
            "id": f"test-guest-id-{i}",
            "provider": "messenger",
            "account_id": f"12345678{i}",
            "account_name": f"test_user_{i}",
            "avatar": f"http://example.com/avatar_{i}.jpg",
            "last_message_at": datetime.now().isoformat(),
            "last_message": {"text": f"Hello world {i}"},
            "assigned_to": (
                CHAT_ASSIGNMENT.AI.value if i < 2 else CHAT_ASSIGNMENT.ME.value
            ),
            "info": guest_info_dict,
            "info_id": guest_info_dict["id"],
        }

        guests.append(guest_dict)
    return guests


@pytest.fixture
def mock_chat_list():
    """Create a list of mock Chat objects for testing."""
    chats = []
    for i in range(3):
        chat = Chat(
            id=f"test-chat-id-{i}",
            guest_id="test-guest-id",
            content={
                "side": "client" if i % 2 == 0 else "staff",
                "message": {"text": f"Hello {i}"},
            },
            created_at=datetime.now(),
        )
        chats.append(chat)
    return chats
