def remove_duplicate_names(rows):
    """
    Remove duplicate food entries based on the normalized 'name' field.
    Keeps the first occurrence.
    """
    seen = set()
    unique_rows = []

    for row in rows:
        name = row.get("name", "")

        if name not in seen:
            seen.add(name)
            unique_rows.append(row)

    return unique_rows
