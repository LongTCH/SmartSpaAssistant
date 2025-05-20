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

# Create a mock for fastapi.encoders to handle circular references


def mock_jsonable_encoder(obj, *args, **kwargs):
    """A custom implementation of jsonable_encoder that handles circular references."""

    # Track objects we've already processed to avoid circular references
    processed_objects = set()

    def _encode(obj, max_depth=10):
        """Inner function to handle encoding with recursion tracking"""
        # Check recursion depth to avoid excessive stack usage
        if max_depth <= 0:
            return str(obj)

        # Handle None and primitive types directly
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Check if we've seen this object before (circular reference)
        obj_id = id(obj)
        if obj_id in processed_objects:
            # Return a simplified representation for circular references
            return f"<Circular:{type(obj).__name__}>"

        # Add this object to our processed set
        processed_objects.add(obj_id)

        try:
            # Handle date/datetime - convert to ISO format string
            if hasattr(obj, "isoformat"):
                return obj.isoformat()

            # Handle dictionaries
            elif isinstance(obj, dict):
                return {k: _encode(v, max_depth - 1) for k, v in obj.items()}

            # Handle lists and tuples
            elif isinstance(obj, (list, tuple, set)):
                return [_encode(item, max_depth - 1) for item in obj]

            # Handle objects from our models
            elif hasattr(obj, "__dict__"):
                result = {}

                # Special handling for Guest objects
                if hasattr(obj, "assigned_to") and hasattr(obj, "info"):
                    # This is likely a Guest object
                    for key, value in obj.__dict__.items():
                        if (
                            key != "info"
                        ):  # Skip the full info object to avoid circular reference
                            result[key] = _encode(value, max_depth - 1)
                    # Just include the info_id reference
                    if hasattr(obj, "info_id"):
                        result["info_id"] = obj.info_id
                    return result

                # Special handling for GuestInfo objects
                elif hasattr(obj, "fullname") and hasattr(obj, "guest"):
                    # This is likely a GuestInfo object
                    for key, value in obj.__dict__.items():
                        if (
                            key != "guest"
                        ):  # Skip the guest object to avoid circular reference
                            result[key] = _encode(value, max_depth - 1)
                    return result

                # Generic object handling
                for key, value in obj.__dict__.items():
                    # Skip private attributes
                    if not key.startswith("_"):
                        result[key] = _encode(value, max_depth - 1)
                return result

            # If all else fails, convert to string
            return str(obj)

        finally:
            # Remove from processed objects when done with this branch
            processed_objects.remove(obj_id)

    # Start the encoding process
    return _encode(obj)


# Patch fastapi.encoders
sys.modules["fastapi.encoders"] = MagicMock()
sys.modules["fastapi.encoders"].jsonable_encoder = mock_jsonable_encoder
