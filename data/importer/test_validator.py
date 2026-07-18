from validator import validate_food

valid_food = {
    "id": "apple",
    "display_name": "Apple",
    "category": "fruits",
    "type": "fruit",
    "aliases": [],
    "usda": "",
    "recognizable": True,
}

invalid_food = {
    "id": "apple",
    "display_name": "Apple",
    "category": "fruits",
    "type": "fruit",
    "aliases": "apple, red apple",
    "usda": 12345,
    "recognizable": "True",
}

print("VALID FOOD")
print(validate_food(valid_food))

print()

print("INVALID FOOD")
print(validate_food(invalid_food))