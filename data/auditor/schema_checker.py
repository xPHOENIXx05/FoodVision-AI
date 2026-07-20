"""Collection loading and schema validation for FoodVision foods."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IMPORTER_DIR = Path(__file__).resolve().parents[1] / "importer"

if str(IMPORTER_DIR) not in sys.path:
    sys.path.append(str(IMPORTER_DIR))

from validator import validate_food


FOODS_KEY = "foods"
REQUIRED_FOOD_FIELDS = (
    "id",
    "display_name",
    "category",
    "type",
    "aliases",
    "recognizable",
    "usda",
)
VALID_CATEGORIES = {
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
}
VALID_TYPES = {
    "food",
}


@dataclass(frozen=True)
class CollectionData:
    """Loaded knowledge-base collection data."""

    filename: str
    path: Path
    foods: list[Any]
    errors: list[str]


@dataclass(frozen=True)
class ValidationIssue:
    """A schema or category validation issue for one food entry."""

    collection: str
    index: int
    food_id: str
    message: str


def load_collection(collection_path: Path, filename: str) -> CollectionData:
    """Load one collection file without modifying it."""

    if not collection_path.exists():
        return CollectionData(
            filename=filename,
            path=collection_path,
            foods=[],
            errors=[f"Collection file not found: {filename}"],
        )

    try:
        with collection_path.open("r", encoding="utf-8") as f:
            collection = json.load(f)
    except json.JSONDecodeError as exc:
        return CollectionData(
            filename=filename,
            path=collection_path,
            foods=[],
            errors=[f"Invalid JSON in {filename}: {exc}"],
        )

    if isinstance(collection, list):
        return CollectionData(
            filename=filename,
            path=collection_path,
            foods=collection,
            errors=[],
        )

    if not isinstance(collection, dict):
        return CollectionData(
            filename=filename,
            path=collection_path,
            foods=[],
            errors=[f"{filename} must be a JSON object or list"],
        )

    foods = collection.get(FOODS_KEY)

    if not isinstance(foods, list):
        return CollectionData(
            filename=filename,
            path=collection_path,
            foods=[],
            errors=[f"{filename} must contain a '{FOODS_KEY}' list"],
        )

    return CollectionData(
        filename=filename,
        path=collection_path,
        foods=foods,
        errors=[],
    )


def load_collections(
    knowledge_base_dir: Path,
    collection_filenames: list[str],
) -> list[CollectionData]:
    """Load all manifest-referenced collections."""

    return [
        load_collection(knowledge_base_dir / filename, filename)
        for filename in collection_filenames
    ]


def food_label(food: Any) -> str:
    """Return a stable label for reporting a food record."""

    if not isinstance(food, dict):
        return "<invalid>"

    food_id = food.get("id")

    if isinstance(food_id, str) and food_id.strip():
        return food_id

    return "<missing id>"


def validate_with_existing_validator(food: dict[str, Any]) -> list[str]:
    """Run the existing validator while allowing USDA null in the auditor."""

    validator_food = dict(food)

    if validator_food.get("usda") is None:
        validator_food["usda"] = ""

    result = validate_food(validator_food)
    return list(result["errors"])


def validate_required_fields(
    collection: str,
    index: int,
    food: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate required FoodVision fields and value types."""

    issues: list[ValidationIssue] = []
    label = food_label(food)

    for field in REQUIRED_FOOD_FIELDS:
        if field not in food:
            issues.append(
                ValidationIssue(
                    collection=collection,
                    index=index,
                    food_id=label,
                    message=f"Missing required field: {field}",
                )
            )

    string_fields = ("id", "display_name", "category", "type")

    for field in string_fields:
        if field not in food:
            continue

        value = food[field]

        if not isinstance(value, str):
            issues.append(
                ValidationIssue(
                    collection=collection,
                    index=index,
                    food_id=label,
                    message=f"{field} must be a string",
                )
            )
        elif not value.strip():
            issues.append(
                ValidationIssue(
                    collection=collection,
                    index=index,
                    food_id=label,
                    message=f"{field} must not be empty",
                )
            )

    if "aliases" in food and not isinstance(food["aliases"], list):
        issues.append(
            ValidationIssue(
                collection=collection,
                index=index,
                food_id=label,
                message="aliases must be a list",
            )
        )

    if "recognizable" in food and not isinstance(food["recognizable"], bool):
        issues.append(
            ValidationIssue(
                collection=collection,
                index=index,
                food_id=label,
                message="recognizable must be a boolean",
            )
        )

    if "usda" in food and food["usda"] is not None and not isinstance(food["usda"], str):
        issues.append(
            ValidationIssue(
                collection=collection,
                index=index,
                food_id=label,
                message="usda must be a string or null",
            )
        )

    return issues


def validate_food_values(
    collection: str,
    index: int,
    food: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate known FoodVision field values."""

    issues: list[ValidationIssue] = []
    label = food_label(food)

    food_type = food.get("type")

    if isinstance(food_type, str) and food_type not in VALID_TYPES:
        issues.append(
            ValidationIssue(
                collection=collection,
                index=index,
                food_id=label,
                message=f"Invalid type: {food_type}",
            )
        )

    recognizable = food.get("recognizable")

    if recognizable is False:
        issues.append(
            ValidationIssue(
                collection=collection,
                index=index,
                food_id=label,
                message="recognizable must be true",
            )
        )

    return issues


def validate_category(
    collection: str,
    index: int,
    food: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate that a food category is supported by FoodVision."""

    category = food.get("category")

    if not isinstance(category, str) or not category.strip():
        return []

    if category in VALID_CATEGORIES:
        return []

    return [
        ValidationIssue(
            collection=collection,
            index=index,
            food_id=food_label(food),
            message=f"Unknown category: {category}",
        )
    ]


def validate_collections(
    collections: list[CollectionData],
) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    """Validate all foods and return schema issues plus category issues."""

    schema_issues: list[ValidationIssue] = []
    category_issues: list[ValidationIssue] = []

    for collection in collections:
        for index, food in enumerate(collection.foods):
            if not isinstance(food, dict):
                schema_issues.append(
                    ValidationIssue(
                        collection=collection.filename,
                        index=index,
                        food_id="<invalid>",
                        message="Food entry must be a JSON object",
                    )
                )
                continue

            seen_messages = set()

            for message in validate_with_existing_validator(food):
                issue = ValidationIssue(
                    collection=collection.filename,
                    index=index,
                    food_id=food_label(food),
                    message=message,
                )
                schema_issues.append(issue)
                seen_messages.add(message)

            for issue in validate_required_fields(collection.filename, index, food):
                if issue.message not in seen_messages:
                    schema_issues.append(issue)
                    seen_messages.add(issue.message)

            for issue in validate_food_values(collection.filename, index, food):
                if issue.message not in seen_messages:
                    schema_issues.append(issue)
                    seen_messages.add(issue.message)

            category_issues.extend(
                validate_category(collection.filename, index, food)
            )

    return schema_issues, category_issues
