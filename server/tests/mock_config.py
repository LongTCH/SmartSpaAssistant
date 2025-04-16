"""Module to setup mock configurations that must be in place before other modules are imported"""

# Create mock for qdrant_client module
import sys
from unittest.mock import MagicMock

# Create a mock for the qdrant_client module
mock_qdrant_client = MagicMock()
mock_qdrant_client.collection_exists.return_value = True

# Patch the module before it's imported anywhere else
sys.modules["qdrant_client"] = MagicMock()
sys.modules["qdrant_client.qdrant_client"] = MagicMock()
sys.modules["qdrant_client.models"] = MagicMock()
sys.modules["qdrant_client.http"] = MagicMock()
sys.modules["qdrant_client.http.models"] = MagicMock()
sys.modules["qdrant_client.http.exceptions"] = MagicMock()

# Add the client attribute
sys.modules["qdrant_client"].QdrantClient = MagicMock
sys.modules["qdrant_client.qdrant_client"].QdrantClient = MagicMock
