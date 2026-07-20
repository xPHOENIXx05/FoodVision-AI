"""Import vegetable metadata into the FoodVision knowledge base."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from collection_validator import validate_collection
from deduplicator import remove_duplicate_names
from normalizer import normalize_name
from schema_mapper import generate_id
from source_loader import load_source
from validator import validate_food
from writer import write_collection


VEGETABLE_CATEGORY = "vegetables"
VEGETABLE_TYPE = "food"
FOODS_KEY = "foods"
RECORD_LIST_KEYS = (
    FOODS_KEY,
    "records",
    "items",
    "vegetables",
)
NAME_FIELDS = (
    "name",
    "vegetable",
    "label",
    "title",
    "display_name",
    "common_name",
)


def extract_records(source_data: Any) -> list[dict[str, Any]]:
    """Extract vegetable records from a loaded CSV or JSON source."""

    if isinstance(source_data, list):
        return source_data

    if isinstance(source_data, dict):
        for key in RECORD_LIST_KEYS:
            value = source_data.get(key)

            if isinstance(value, list):
                return value

        for value in source_data.values():
            if isinstance(value, list):
                return value

    raise ValueError("Vegetable source must be a list or contain a list of records")


def normalize_record(record: dict[str, Any]) -> dict[str, str] | None:
    """Normalize a source record into the importer row format."""

    for field in NAME_FIELDS:
        value = record.get(field)

        if isinstance(value, str) and value.strip():
            name = value
            break
    else:
        return None

    return {
        "name": normalize_name(name),
    }


def map_vegetable_to_food(row: dict[str, str]) -> dict[str, Any]:
    """Convert a normalized vegetable row into a FoodVision food object."""

    display_name = row["name"]

    return {
        "id": generate_id(display_name),
        "display_name": display_name,
        "category": VEGETABLE_CATEGORY,
        "type": VEGETABLE_TYPE,
        "aliases": [],
        "recognizable": True,
        "usda": None,
    }


def validate_vegetable_food(food: dict[str, Any]) -> list[str]:
    """Validate a vegetable food entry using the existing FoodVision validator."""

    validator_food = dict(food)
    validator_food["usda"] = ""

    result = validate_food(validator_food)
    errors = list(result["errors"])

    if food.get("usda") is not None:
        errors.append("usda must be null for vegetable imports")

    return errors


def load_vegetable_collection(collection_path: Path) -> tuple[Any, list[dict[str, Any]]]:
    """Load vegetables.json and return the original payload plus its foods list."""

    if not collection_path.exists():
        collection = {
            "schema_version": 1,
            FOODS_KEY: [],
        }
        return collection, collection[FOODS_KEY]

    collection = load_source(collection_path)

    if isinstance(collection, list):
        return collection, collection

    if not isinstance(collection, dict):
        raise ValueError(f"Invalid vegetables collection format: {collection_path}")

    foods = collection.get(FOODS_KEY)

    if foods is None:
        collection[FOODS_KEY] = []
        foods = collection[FOODS_KEY]
    elif not isinstance(foods, list):
        raise ValueError(f"vegetables.json foods must be a list: {collection_path}")

    return collection, foods


def existing_vegetable_keys(foods: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """Return existing vegetable ids and normalized display names."""

    ids: set[str] = set()
    display_names: set[str] = set()

    for food in foods:
        food_id = food.get("id")
        display_name = food.get("display_name")

        if food_id:
            ids.add(food_id)

        if isinstance(display_name, str):
            normalized_name = normalize_name(display_name)
            display_names.add(normalized_name.casefold())

    return ids, display_names


def print_vegetable_summary(
    records_read: int,
    imported: int,
    duplicates: int,
    invalid: int,
) -> None:
    """Print a concise vegetable import summary."""

    skipped = duplicates + invalid

    print("=" * 38)
    print("Vegetable Import Summary")
    print("=" * 38)
    print()
    print(f"{'Records Read:':<20}{records_read:>8}")
    print(f"{'Imported:':<20}{imported:>8}")
    print(f"{'Skipped:':<20}{skipped:>8}")
    print()
    print(f"{'Duplicates:':<20}{duplicates:>8}")
    print(f"{'Invalid:':<20}{invalid:>8}")
    print()
    print("=" * 38)


def import_vegetables(
    source_path: Path,
    knowledge_base_dir: Path,
    dry_run: bool = False,
) -> dict[str, int]:
    """Import vegetable metadata into knowledge_base/vegetables.json."""

    source_data = load_source(source_path)
    records = extract_records(source_data)

    normalized_rows: list[dict[str, str]] = []
    invalid = 0

    for record in records:
        if not isinstance(record, dict):
            invalid += 1
            continue

        normalized_row = normalize_record(record)

        if normalized_row is None:
            invalid += 1
            continue

        normalized_rows.append(normalized_row)

    unique_rows = remove_duplicate_names(normalized_rows)
    duplicates = len(normalized_rows) - len(unique_rows)

    collection_path = knowledge_base_dir / "vegetables.json"
    collection, foods = load_vegetable_collection(collection_path)
    existing_ids, existing_display_names = existing_vegetable_keys(foods)

    imported = 0

    for row in unique_rows:
        food = map_vegetable_to_food(row)
        normalized_display_name = normalize_name(food["display_name"]).casefold()

        if food["id"] in existing_ids or normalized_display_name in existing_display_names:
            duplicates += 1
            continue

        errors = validate_vegetable_food(food)

        if errors:
            invalid += 1
            continue

        foods.append(food)
        existing_ids.add(food["id"])
        existing_display_names.add(normalized_display_name)
        imported += 1

    if imported:
        result = validate_collection(foods)

        if not result["valid"]:
            raise ValueError(
                "Invalid vegetables collection: "
                + ", ".join(result["errors"])
            )

        if not dry_run:
            write_collection(collection_path, collection)

    print_vegetable_summary(
        records_read=len(records),
        imported=imported,
        duplicates=duplicates,
        invalid=invalid,
    )

    return {
        "records_read": len(records),
        "imported": imported,
        "skipped": duplicates + invalid,
        "duplicates": duplicates,
        "invalid": invalid,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the vegetable importer."""

    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Import vegetable metadata into FoodVision."
    )
    parser.add_argument(
        "source_path",
        nargs="?",
        type=Path,
        default=project_root / "data" / "imports" / "vegetables.csv",
        help="Path to a CSV or JSON vegetable dataset.",
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
        help="Validate and summarize without writing vegetables.json.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import_vegetables(
        source_path=args.source_path,
        knowledge_base_dir=args.knowledge_base_dir,
        dry_run=args.dry_run,
    )
