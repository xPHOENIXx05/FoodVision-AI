def validate_collection(foods):
    """
    Validate an entire food collection.

    Checks:
    - Duplicate IDs
    - Duplicate display names
    """

    errors = []

    seen_ids = set()
    seen_names = set()

    for food in foods:

        food_id = food["id"]
        display_name = food["display_name"]

        if food_id in seen_ids:
            errors.append(f"Duplicate id: {food_id}")
        else:
            seen_ids.add(food_id)

        if display_name in seen_names:
            errors.append(f"Duplicate display_name: {display_name}")
        else:
            seen_names.add(display_name)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }