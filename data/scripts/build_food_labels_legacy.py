import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CATEGORIES_DIR = BASE_DIR / "categories"
OUTPUT_FILE = BASE_DIR / "food_labels.json"

all_foods = []
category_stats = {}

# Read every JSON file in the categories folder
for json_file in sorted(CATEGORIES_DIR.glob("*.json")):

    category_name = json_file.stem

    print(f"Loading {json_file.name}...")

    with open(json_file, "r", encoding="utf-8") as f:

        foods = json.load(f)

        if not isinstance(foods, list):
            raise ValueError(f"{json_file.name} must contain a JSON array.")

        category_stats[category_name] = len(foods)

        all_foods.extend(foods)

# Validate and remove duplicate labels
unique_foods = {}

for food in all_foods:

    # Required fields
    if "label" not in food:
        raise ValueError(f"Missing 'label' field: {food}")

    if "usda" not in food:
        raise ValueError(f"Missing 'usda' field: {food}")

    label = food["label"].strip().lower()
    usda = food["usda"].strip()

    if not label:
        raise ValueError("Food label cannot be empty.")

    if not usda:
        raise ValueError(f"USDA mapping missing for '{label}'.")

    if label not in unique_foods:
        unique_foods[label] = {
            "label": food["label"].strip(),
            "usda": usda
        }
    else:
        print(f"Duplicate label skipped: {label}")
        
# Sort alphabetically
final_foods = sorted(
    unique_foods.values(),
    key=lambda x: x["label"].lower()
)

# Save output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_foods, f, indent=4, ensure_ascii=False)

print("\n========== Food Database ==========")

for category, count in sorted(category_stats.items()):
    print(f"{category:<20} {count}")

print("-----------------------------------")
print(f"Categories         : {len(category_stats)}")
print(f"Foods Loaded       : {len(all_foods)}")
print(f"Foods Saved        : {len(final_foods)}")
print(f"Output             : {OUTPUT_FILE}")
print("===================================")