from deduplicator import remove_duplicate_names

rows = [
    {"name": "Apple"},
    {"name": "Banana"},
    {"name": "Apple"},
    {"name": "Orange"},
    {"name": "Banana"},
    {"name": "Mango"},
]

result = remove_duplicate_names(rows)

print(result)