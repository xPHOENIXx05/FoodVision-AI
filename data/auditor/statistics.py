"""Reusable statistics for FoodVision knowledge-base audits."""

from __future__ import annotations

from dataclasses import dataclass

from duplicate_checker import DuplicateIssue
from manifest_checker import ManifestResult
from schema_checker import CollectionData, ValidationIssue


@dataclass(frozen=True)
class AuditStatistics:
    """Computed audit statistics."""

    total_collections: int
    total_foods: int
    foods_per_collection: dict[str, int]
    duplicate_ids: int
    duplicate_names: int
    schema_errors: int
    manifest_errors: int
    collection_errors: int
    unknown_categories: int
    foods_missing_usda: int
    recognizable_false: int


def build_statistics(
    manifest_result: ManifestResult,
    collections: list[CollectionData],
    schema_issues: list[ValidationIssue],
    category_issues: list[ValidationIssue],
    duplicate_ids: list[DuplicateIssue],
    duplicate_names: list[DuplicateIssue],
) -> AuditStatistics:
    """Build summary statistics for an audit result."""

    foods_per_collection = {
        collection.filename: len(collection.foods)
        for collection in collections
    }
    total_foods = sum(foods_per_collection.values())
    collection_errors = sum(len(collection.errors) for collection in collections)
    foods_missing_usda = 0
    recognizable_false = 0

    for collection in collections:
        for food in collection.foods:
            if not isinstance(food, dict):
                continue

            if food.get("usda") is None:
                foods_missing_usda += 1

            if food.get("recognizable") is False:
                recognizable_false += 1

    return AuditStatistics(
        total_collections=len(collections),
        total_foods=total_foods,
        foods_per_collection=foods_per_collection,
        duplicate_ids=len(duplicate_ids),
        duplicate_names=len(duplicate_names),
        schema_errors=len(schema_issues),
        manifest_errors=len(manifest_result.errors),
        collection_errors=collection_errors,
        unknown_categories=len(category_issues),
        foods_missing_usda=foods_missing_usda,
        recognizable_false=recognizable_false,
    )


def audit_passed(statistics: AuditStatistics) -> bool:
    """Return whether the audit passed integrity checks."""

    return (
        statistics.duplicate_ids == 0
        and statistics.duplicate_names == 0
        and statistics.schema_errors == 0
        and statistics.manifest_errors == 0
        and statistics.collection_errors == 0
        and statistics.unknown_categories == 0
    )
