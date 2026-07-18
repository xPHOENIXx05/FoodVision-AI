import re


def generate_id(display_name: str) -> str:
    """
    Convert a display name into a stable ID.
    Example:
        "Red Delicious Apple" -> "red_delicious_apple"
    """
    text = display_name.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def map_to_schema(row, category, food_type):
    """
    Convert an imported row into the FoodVision AI schema.
    """
    display_name = row["name"]

    return {
        "id": generate_id(display_name),
        "display_name": display_name,
        "category": category,
        "type": food_type,
        "aliases": [],
        "usda": "",
        "recognizable": True,
    }