from collection_validator import validate_collection

foods = [
    {
        "id": "apple",
        "display_name": "Apple",
    },
    {
        "id": "banana",
        "display_name": "Banana",
    },
    {
        "id": "apple",
        "display_name": "Green Apple",
    },
    {
        "id": "green_apple",
        "display_name": "Apple",
    },
]

result = validate_collection(foods)

print(result)