REQUIRED_FIELDS = [
    "id",
    "display_name",
    "category",
    "type",
]


def validate_food(food):
    """
    Validate a FoodVision AI food record.
    """

    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        value = food.get(field)

        if value is None:
            errors.append(f"Missing required field: {field}")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Empty required field: {field}")

    # Validate field types
    if "aliases" in food and not isinstance(food["aliases"], list):
        errors.append("aliases must be a list")

    if "usda" in food and not isinstance(food["usda"], str):
        errors.append("usda must be a string")

    if "recognizable" in food and not isinstance(food["recognizable"], bool):
        errors.append("recognizable must be a boolean")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }