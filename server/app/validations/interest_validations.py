import re


def validate_interest_data(interest: dict):
    """
    Validate interest data according to business rules:
    - name: must not be empty
    - color: must be 7 characters, start with '#', positions 2-7 must be valid hex (0-9, A-F)

    Args:
        interest: Dictionary containing interest data

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    name = interest.get("name", "")
    color = interest.get("color", "")

    # Validate name
    if not name or not str(name).strip():
        errors.append("Name must not be empty.")

    # Validate color
    if not color:
        errors.append("Color must not be empty.")
    else:
        color_str = str(color).strip()
        if len(color_str) != 7:
            errors.append("Color must be exactly 7 characters long.")
        elif not color_str.startswith("#"):
            errors.append("Color must start with '#'.")
        elif not re.match(r"^#[0-9A-Fa-f]{6}$", color_str):
            errors.append("Color must be a valid hex color code (e.g., #FF5733).")

    return errors
