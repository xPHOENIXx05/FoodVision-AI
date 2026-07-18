from schema_mapper import map_to_schema

row = {"name": "Red Delicious Apple"}

food = map_to_schema(
    row,
    category="fruits",
    food_type="fruit"
)

print(food)