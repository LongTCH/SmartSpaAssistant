def validate_script_data(script: dict):
    """
    Validate script data according to business rules:
    - name: must not be empty
    - description: must not be empty
    - solution: must not be empty

    Args:
        script: Dictionary containing script data

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    name = script.get("name", "")
    description = script.get("description", "")
    solution = script.get("solution", "")

    # Validate name
    if not name or not str(name).strip():
        errors.append("Name must not be empty.")

    # Validate description
    if not description or not str(description).strip():
        errors.append("Description must not be empty.")

    # Validate solution
    if not solution or not str(solution).strip():
        errors.append("Solution must not be empty.")

    return errors
