def normalize_name(name: str) -> str:
    """
    Normalize a food name for consistent storage.
    """

    if not name:
        return ""

    # Remove extra whitespace
    name = " ".join(name.strip().split())

    # Convert to Title Case
    return name.title()
