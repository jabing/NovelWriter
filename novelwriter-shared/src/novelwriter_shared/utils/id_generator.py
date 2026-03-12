"""ID generation utilities."""

import uuid


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string with optional prefix
    """
    unique_id = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id
