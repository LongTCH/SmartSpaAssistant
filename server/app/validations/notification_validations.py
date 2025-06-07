ALLOWED_PARAM_TYPES = ["String", "Integer", "Numeric", "Boolean", "DateTime"]


def validate_notification_data(notification: dict):
    errors = []
    label = notification.get("label", "")
    description = notification.get("description", "")
    params = notification.get("params", [])
    # Handle None or empty label
    if not label or not str(label).strip() or not (1 <= len(str(label).strip()) <= 40):
        errors.append("Label must be 1-40 characters long.")
    if not description or not str(description).strip():
        errors.append("Description must not be empty.")
    for idx, param in enumerate(params):
        pname = param.get("param_name", "")
        pdesc = param.get("description", "")
        ptype = param.get("param_type", "")
        if not pname or not str(pname).strip():
            errors.append(f"ParamName at index {idx} must not be empty.")
        if not pdesc or not str(pdesc).strip():
            errors.append(f"ParamDescription at index {idx} must not be empty.")
        if ptype not in ALLOWED_PARAM_TYPES:
            errors.append(
                f"ParamType at index {idx} must be one of {ALLOWED_PARAM_TYPES}."
            )
    return errors
