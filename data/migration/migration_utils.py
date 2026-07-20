"""Utilities for the one-time FoodVision v1-to-v2 knowledge-base migration."""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from migration_report import MigrationStats


IMPORTER_DIR = Path(__file__).resolve().parents[1] / "importer"

if str(IMPORTER_DIR) not in sys.path:
    sys.path.append(str(IMPORTER_DIR))

from collection_validator import validate_collection
from normalizer import normalize_name
from schema_mapper import generate_id
from source_loader import load_source
from validator import validate_food
from writer import write_collection


FOODS_KEY = "foods"
MANIFEST_FILE = "manifest.json"
SUPPORTED_CATEGORIES = (
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
)
SUPPORTED_CATEGORY_SET = set(SUPPORTED_CATEGORIES)
CATEGORY_ALIASES = {
    "fruit": "fruits",
    "fruits": "fruits",
    "vegetable": "vegetables",
    "vegetables": "vegetables",
    "protein": "proteins",
    "proteins": "proteins",
    "seafood": "seafood",
    "dairy": "dairy",
    "grain": "grains",
    "grains": "grains",
    "dessert": "desserts",
    "desserts": "desserts",
    "drink": "drinks",
    "drinks": "drinks",
    "snack": "snacks",
    "snacks": "snacks",
    "fast food": "fast_food",
    "fast foods": "fast_food",
    "restaurant food": "restaurant_foods",
    "restaurant foods": "restaurant_foods",
    "street food": "street_foods",
    "street foods": "street_foods",
    "regional": "regional_foods",
    "regional food": "regional_foods",
    "regional foods": "regional_foods",
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


@dataclass
class CollectionFile:
    """Loaded knowledge-base collection with its original shape."""

    filename: str
    path: Path
    payload: Any
    foods: list[dict[str, Any]]
    is_list: bool


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for change detection."""

    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def load_manifest(knowledge_base_dir: Path) -> dict[str, Any]:
    """Load knowledge_base/manifest.json."""

    manifest = load_source(knowledge_base_dir / MANIFEST_FILE)

    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be a JSON object")

    collections = manifest.get("collections")

    if not isinstance(collections, list):
        raise ValueError("manifest.json must contain a collections list")

    return manifest


def load_collection(knowledge_base_dir: Path, filename: str) -> CollectionFile:
    """Load a collection file while preserving list or wrapper shape."""

    path = knowledge_base_dir / filename
    payload = load_source(path)

    if isinstance(payload, list):
        foods = payload
        is_list = True
    elif isinstance(payload, dict):
        raw_foods = payload.get(FOODS_KEY)

        if not isinstance(raw_foods, list):
            raise ValueError(f"{filename} must contain a '{FOODS_KEY}' list")

        foods = raw_foods
        is_list = False
    else:
        raise ValueError(f"{filename} must be a JSON object or list")

    return CollectionFile(
        filename=filename,
        path=path,
        payload=payload,
        foods=foods,
        is_list=is_list,
    )


def collection_payload(collection: CollectionFile, foods: list[dict[str, Any]]) -> Any:
    """Build a writable payload using the collection's original shape."""

    if collection.is_list:
        return foods

    payload = deepcopy(collection.payload)
    payload[FOODS_KEY] = foods
    return payload


def new_collection_payload(foods: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a wrapper payload for a new collection."""

    return {
        "schema_version": 1,
        FOODS_KEY: foods,
    }


def normalize_category_value(value: Any, source_filename: str) -> str:
    """Convert legacy category values to supported FoodVision categories."""

    if isinstance(value, str) and value.strip():
        key = " ".join(
            value.strip().lower().replace("_", " ").split()
        )

        if key in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[key]

        if value.strip() in SUPPORTED_CATEGORY_SET:
            return value.strip()

    source_category = Path(source_filename).stem

    if source_category in SUPPORTED_CATEGORY_SET:
        return source_category

    raise ValueError(
        f"Unable to infer supported category for record in {source_filename}"
    )


def display_name_from_food(food: dict[str, Any]) -> str:
    """Return a normalized display name, inferring it from id when needed."""

    display_name = food.get("display_name")

    if isinstance(display_name, str) and display_name.strip():
        return normalize_name(display_name)

    food_id = food.get("id")

    if isinstance(food_id, str) and food_id.strip():
        return normalize_name(food_id.replace("_", " "))

    raise ValueError("Food record must contain display_name or id")


def normalize_aliases(value: Any) -> list[str]:
    """Normalize aliases while preserving useful values."""

    if isinstance(value, list):
        return [
            alias
            for alias in value
            if isinstance(alias, str) and alias.strip()
        ]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def is_valid_id(food_id: Any, display_name: str) -> bool:
    """Return whether a food id is valid and consistent with display_name."""

    if not isinstance(food_id, str) or not food_id.strip():
        return False

    return bool(ID_PATTERN.fullmatch(food_id)) and food_id == generate_id(display_name)


def migrate_food(
    food: dict[str, Any],
    source_filename: str,
    stats: MigrationStats,
) -> tuple[str, dict[str, Any]]:
    """Migrate one food entry to the current FoodVision schema."""

    changed = False
    missing_fields = 0

    display_was_missing = "display_name" not in food
    display_name = display_name_from_food(food)

    if display_was_missing:
        missing_fields += 1
        changed = True
    elif food.get("display_name") != display_name:
        stats.display_names_normalized += 1
        changed = True

    category_was_missing = "category" not in food
    category = normalize_category_value(food.get("category"), source_filename)

    if category_was_missing:
        missing_fields += 1
        changed = True
    elif food.get("category") != category:
        stats.categories_standardized += 1
        changed = True

    food_id = food.get("id")

    if "id" not in food:
        missing_fields += 1
        changed = True

    if not is_valid_id(food_id, display_name):
        food_id = generate_id(display_name)
        stats.ids_regenerated += 1
        changed = True

    food_type = food.get("type")

    if "type" not in food:
        missing_fields += 1
        changed = True
    elif food_type != "food":
        stats.types_standardized += 1
        changed = True

    aliases = normalize_aliases(food.get("aliases"))

    if "aliases" not in food:
        missing_fields += 1
        changed = True
    elif aliases != food.get("aliases"):
        changed = True

    recognizable = food.get("recognizable")

    if "recognizable" not in food:
        missing_fields += 1
        recognizable = True
        changed = True
    elif recognizable is not True:
        recognizable = True
        changed = True

    usda = food.get("usda")

    if "usda" not in food:
        missing_fields += 1
        usda = None
        changed = True
    elif usda == "":
        usda = None
        stats.usda_standardized += 1
        changed = True

    migrated = {
        "id": food_id,
        "display_name": display_name,
        "category": category,
        "type": "food",
        "aliases": aliases,
        "recognizable": recognizable,
        "usda": usda,
    }

    for key, value in food.items():
        if key not in migrated:
            migrated[key] = value

    stats.missing_fields_added += missing_fields

    if changed:
        stats.foods_updated += 1

    return f"{category}.json", migrated


def merge_aliases(primary: list[str], duplicate: list[str]) -> list[str]:
    """Merge alias lists while preserving order."""

    merged: list[str] = []
    seen: set[str] = set()

    for alias in primary + duplicate:
        key = alias.casefold()

        if key not in seen:
            merged.append(alias)
            seen.add(key)

    return merged


def has_usda_value(value: Any) -> bool:
    """Return whether a USDA value contains useful data."""

    return isinstance(value, str) and bool(value.strip())


def merge_foods(
    primary: dict[str, Any],
    duplicate: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Merge useful duplicate food metadata into the primary record."""

    merged = dict(primary)
    changed = False
    aliases = merge_aliases(
        normalize_aliases(primary.get("aliases")),
        normalize_aliases(duplicate.get("aliases")),
    )

    if aliases != primary.get("aliases"):
        merged["aliases"] = aliases
        changed = True

    if not has_usda_value(primary.get("usda")) and has_usda_value(duplicate.get("usda")):
        merged["usda"] = duplicate["usda"]
        changed = True
    elif primary.get("usda") == "":
        merged["usda"] = None
        changed = True

    if primary.get("recognizable") is not True and duplicate.get("recognizable") is True:
        merged["recognizable"] = True
        changed = True

    return merged, changed


def deduplicate_foods(
    candidates: list[tuple[str, dict[str, Any]]],
    stats: MigrationStats,
) -> dict[str, list[dict[str, Any]]]:
    """Remove duplicate foods across the full knowledge base."""

    merged: list[tuple[str, dict[str, Any]]] = []
    id_index: dict[str, int] = {}
    name_index: dict[str, int] = {}

    for target_filename, food in candidates:
        food_id = food["id"]
        display_name_key = food["display_name"].casefold()
        match_indexes = []

        if food_id in id_index:
            match_indexes.append(id_index[food_id])

        if display_name_key in name_index:
            match_indexes.append(name_index[display_name_key])

        if not match_indexes:
            index = len(merged)
            merged.append((target_filename, food))
            id_index[food_id] = index
            name_index[display_name_key] = index
            continue

        primary_index = min(match_indexes)
        primary_filename, primary_food = merged[primary_index]
        merged_food, changed = merge_foods(primary_food, food)
        merged[primary_index] = (primary_filename, merged_food)
        stats.duplicate_foods_removed += 1

        if changed:
            stats.foods_updated += 1

    grouped = {
        f"{category}.json": []
        for category in SUPPORTED_CATEGORIES
    }

    for target_filename, food in merged:
        grouped.setdefault(target_filename, []).append(food)

    return grouped


def validate_food_for_migration(food: dict[str, Any]) -> list[str]:
    """Validate a migrated food using existing validators where practical."""

    validator_food = dict(food)

    if validator_food.get("usda") is None:
        validator_food["usda"] = ""

    result = validate_food(validator_food)
    errors = list(result["errors"])

    if food.get("category") not in SUPPORTED_CATEGORY_SET:
        errors.append(f"Unknown category: {food.get('category')}")

    if food.get("type") != "food":
        errors.append(f"Invalid type: {food.get('type')}")

    if food.get("recognizable") is not True:
        errors.append("recognizable must be true")

    return errors


def validate_migrated_collections(grouped_foods: dict[str, list[dict[str, Any]]]) -> None:
    """Validate migrated collections before writing."""

    for filename, foods in grouped_foods.items():
        collection_result = validate_collection(foods)

        if not collection_result["valid"]:
            raise ValueError(
                f"Invalid migrated collection {filename}: "
                + ", ".join(collection_result["errors"])
            )

        for food in foods:
            errors = validate_food_for_migration(food)

            if errors:
                raise ValueError(
                    f"Invalid migrated food '{food.get('display_name', '')}' "
                    f"in {filename}: "
                    + ", ".join(errors)
                )


def unique_manifest_collections(collections: list[Any]) -> list[str]:
    """Return valid manifest collection filenames without duplicates."""

    unique: list[str] = []
    seen: set[str] = set()

    for collection in collections:
        if not isinstance(collection, str):
            continue

        filename = collection.strip()

        if not filename or filename in seen:
            continue

        unique.append(filename)
        seen.add(filename)

    return unique


def build_final_manifest(
    manifest: dict[str, Any],
    grouped_foods: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[str]]:
    """Remove obsolete collections from manifest after migration."""

    original_collections = unique_manifest_collections(manifest["collections"])
    final_collections: list[str] = []
    removed_collections: list[str] = []

    for filename in original_collections:
        category = Path(filename).stem

        if category in SUPPORTED_CATEGORY_SET:
            final_collections.append(filename)
        else:
            removed_collections.append(filename)

    for category in SUPPORTED_CATEGORIES:
        filename = f"{category}.json"

        if filename not in final_collections and grouped_foods.get(filename):
            final_collections.append(filename)

    final_manifest = deepcopy(manifest)
    final_manifest["collections"] = final_collections
    return final_manifest, removed_collections


def write_if_changed(path: Path, payload: Any, original_payload: Any | None) -> bool:
    """Write JSON only when the payload changed."""

    if original_payload is not None and canonical_json(payload) == canonical_json(original_payload):
        return False

    write_collection(path, payload)
    return True
