"""Import Food-101 class metadata into the FoodVision knowledge base."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from collection_validator import validate_collection
from deduplicator import remove_duplicate_names
from food101_mapper import FOOD101_COLLECTION_MAP, get_collection, validate_mapping_coverage
from normalizer import normalize_name
from source_loader import load_source
from validator import validate_food
from writer import write_collection


COLLECTION_DISPLAY_ORDER = [
    "fruits",
    "vegetables",
    "proteins",
    "seafood",
    "dairy",
    "grains",
    "desserts",
    "snacks",
    "drinks",
    "fast_food",
    "restaurant_foods",
    "street_foods",
    "regional_foods",
]


def normalize_class_name(class_name: str) -> str:
    """Normalize a Food-101 class name to snake_case."""

    text = class_name.strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    parts = [part for part in text.split("_") if part]
    return "_".join(parts)


def read_class_file(class_file: Path) -> list[str]:
    """Read Food-101 class names from a one-class-per-line text file."""

    if not class_file.exists():
        raise FileNotFoundError(f"Food-101 class file not found: {class_file}")

    with class_file.open("r", encoding="utf-8") as f:
        return [
            normalize_class_name(line)
            for line in f
            if line.strip()
        ]


def display_name_for_class(class_name: str) -> str:
    """Convert a Food-101 class id into a FoodVision display name."""

    return normalize_name(class_name.replace("_", " "))


def map_class_to_food(class_name: str) -> dict[str, Any]:
    """Convert one Food-101 class name into a FoodVision food object."""

    return {
        "id": class_name,
        "display_name": display_name_for_class(class_name),
        "category": get_collection(class_name),
        "type": "food",
        "aliases": [],
        "recognizable": True,
        "usda": None,
    }


def validate_food101_food(food: dict[str, Any]) -> None:
    """Validate a Food-101 food entry using the existing FoodVision validator."""

    validator_food = dict(food)
    validator_food["usda"] = ""

    result = validate_food(validator_food)
    errors = list(result["errors"])

    if food.get("usda") is not None:
        errors.append("usda must be null for Food-101 imports")

    if errors:
        raise ValueError(
            f"Invalid Food-101 food '{food.get('display_name', '')}': "
            + ", ".join(errors)
        )


def load_collection(collection_path: Path) -> dict[str, Any]:
    """Load a knowledge-base collection, preserving its wrapper schema."""

    if not collection_path.exists():
        return {
            "schema_version": 1,
            "foods": [],
        }

    collection = load_source(collection_path)

    if isinstance(collection, list):
        return {
            "schema_version": 1,
            "foods": collection,
        }

    if not isinstance(collection, dict):
        raise ValueError(f"Invalid collection format: {collection_path}")

    foods = collection.get("foods")

    if foods is None:
        collection["foods"] = []
    elif not isinstance(foods, list):
        raise ValueError(f"Collection foods must be a list: {collection_path}")

    return collection


def load_manifest_collections(knowledge_base_dir: Path) -> list[str]:
    """Load knowledge-base collection filenames from manifest.json."""

    manifest_path = knowledge_base_dir / "manifest.json"
    manifest = load_source(manifest_path)

    if not isinstance(manifest, dict):
        raise ValueError(f"Invalid manifest format: {manifest_path}")

    collections = manifest.get("collections")

    if not isinstance(collections, list):
        raise ValueError(f"Manifest collections must be a list: {manifest_path}")

    return collections


def existing_food_keys(knowledge_base_dir: Path) -> tuple[set[str], set[str]]:
    """Return existing food ids and display names from all manifest collections."""

    ids: set[str] = set()
    display_names: set[str] = set()

    for filename in load_manifest_collections(knowledge_base_dir):
        collection_path = knowledge_base_dir / filename

        if not collection_path.exists():
            continue

        collection = load_collection(collection_path)

        for food in collection["foods"]:
            food_id = food.get("id")
            display_name = food.get("display_name")

            if food_id:
                ids.add(food_id)

            if display_name:
                display_names.add(display_name.casefold())

    return ids, display_names


def validate_updated_collection(collection_name: str, foods: list[dict[str, Any]]) -> None:
    """Validate a complete collection before it is written."""

    result = validate_collection(foods)

    if not result["valid"]:
        raise ValueError(
            f"Invalid collection '{collection_name}': "
            + ", ".join(result["errors"])
        )


def format_collection_name(collection_name: str) -> str:
    """Return a human-readable collection name for import reports."""

    return collection_name.replace("_", " ").title()


def print_food101_summary(
    classes_read: int,
    imported: int,
    skipped: int,
    imported_by_collection: Counter[str],
) -> None:
    """Print the Food-101 import summary."""

    print("=" * 38)
    print("Food-101 Import Summary")
    print("=" * 38)
    print()
    print(f"{'Classes Read:':<20}{classes_read:>8}")
    print(f"{'Imported:':<20}{imported:>8}")
    print(f"{'Skipped:':<20}{skipped:>8}")
    print()

    for collection_name in COLLECTION_DISPLAY_ORDER:
        count = imported_by_collection.get(collection_name, 0)

        if count:
            label = f"{format_collection_name(collection_name)}:"
            print(f"{label:<20}{count:>8}")

    print()
    print("=" * 38)


def import_food101(
    class_file: Path,
    knowledge_base_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Import Food-101 class metadata into the knowledge base."""

    class_names = read_class_file(class_file)
    rows = [{"name": class_name} for class_name in class_names]
    unique_rows = remove_duplicate_names(rows)
    unique_class_names = [row["name"] for row in unique_rows]

    validate_mapping_coverage(unique_class_names)

    existing_ids, existing_display_names = existing_food_keys(knowledge_base_dir)
    target_collections = {
        collection_name: load_collection(
            knowledge_base_dir / f"{collection_name}.json"
        )
        for collection_name in sorted(set(FOOD101_COLLECTION_MAP.values()))
    }

    imported_by_collection: Counter[str] = Counter()
    skipped = len(rows) - len(unique_rows)

    for class_name in unique_class_names:
        food = map_class_to_food(class_name)
        display_name_key = food["display_name"].casefold()

        if food["id"] in existing_ids or display_name_key in existing_display_names:
            skipped += 1
            continue

        validate_food101_food(food)

        collection = target_collections[food["category"]]
        collection["foods"].append(food)

        existing_ids.add(food["id"])
        existing_display_names.add(display_name_key)
        imported_by_collection[food["category"]] += 1

    for collection_name, collection in target_collections.items():
        if not imported_by_collection.get(collection_name, 0):
            continue

        foods = collection["foods"]
        validate_updated_collection(collection_name, foods)

        if not dry_run:
            write_collection(
                knowledge_base_dir / f"{collection_name}.json",
                collection,
            )

    imported = sum(imported_by_collection.values())

    print_food101_summary(
        classes_read=len(class_names),
        imported=imported,
        skipped=skipped,
        imported_by_collection=imported_by_collection,
    )

    return {
        "classes_read": len(class_names),
        "imported": imported,
        "skipped": skipped,
        "imported_by_collection": imported_by_collection,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Food-101 importer."""

    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Import Food-101 class metadata into FoodVision."
    )
    parser.add_argument(
        "class_file",
        nargs="?",
        type=Path,
        default=project_root / "food101_classes.txt",
        help="Path to a one-class-per-line Food-101 class file.",
    )
    parser.add_argument(
        "--knowledge-base-dir",
        type=Path,
        default=project_root / "data" / "knowledge_base",
        help="Path to the FoodVision knowledge_base directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and summarize without writing collection files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import_food101(
        class_file=args.class_file,
        knowledge_base_dir=args.knowledge_base_dir,
        dry_run=args.dry_run,
    )
