import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
GENERATED_DIR = BASE_DIR / "generated"

MANIFEST_FILE = KNOWLEDGE_BASE_DIR / "manifest.json"
OUTPUT_FILE = GENERATED_DIR / "food_labels.json"

all_foods = []
category_stats = {}

# Read manifest
with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)

collections = manifest.get("collections", [])

# Read each collection listed in the manifest
for collection in collections:
    json_file = KNOWLEDGE_BASE_DIR / collection

    if not json_file.exists():
        raise FileNotFoundError(f"Collection not found: {collection}")

    category_name = json_file.stem

    print(f"Loading {json_file.name}...")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    foods = data.get("foods")

    if not isinstance(foods, list):
        raise ValueError(f"{json_file.name} must contain a 'foods' array.")

    category_stats[category_name] = len(foods)
    all_foods.extend(foods)

unique_foods = {}

for food in all_foods:

    # Required fields
    required_fields = ["id", "display_name", "category", "aliases", "usda"]

    for field in required_fields:
        if field not in food:
            raise ValueError(f"Missing '{field}' field: {food}")

    label = food["display_name"].strip()
    usda = food["usda"].strip()

    if not label:
        raise ValueError("Display name cannot be empty.")

    if not usda:
        raise ValueError(f"USDA mapping missing for '{label}'.")

    key = label.lower()

    if key not in unique_foods:
        unique_foods[key] = {
            "label": label,
            "usda": usda
        }
    else:
        print(f"Duplicate skipped: {label}")
        
# Sort alphabetically
final_foods = sorted(
    unique_foods.values(),
    key=lambda x: x["label"].lower()
)

# Ensure generated directory exists
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

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