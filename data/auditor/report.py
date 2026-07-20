"""Console reporting for FoodVision knowledge-base audits."""

from __future__ import annotations

from duplicate_checker import DuplicateIssue
from manifest_checker import ManifestResult
from schema_checker import CollectionData, ValidationIssue
from statistics import AuditStatistics, audit_passed


def display_collection_name(filename: str) -> str:
    """Convert a collection filename into a report label."""

    name = filename.removesuffix(".json")
    return name.replace("_", " ").title()


def print_metric(label: str, value: int) -> None:
    """Print one aligned metric row."""

    print(f"{label:<28}{value:>8}")


def print_duplicate_details(title: str, issues: list[DuplicateIssue]) -> None:
    """Print detailed duplicate issue information."""

    if not issues:
        return

    print(title)

    for issue in issues:
        print(f"- {issue.value}")
        print(f"  Locations: {', '.join(issue.locations)}")

    print()


def print_validation_details(title: str, issues: list[ValidationIssue]) -> None:
    """Print detailed schema or category validation issues."""

    if not issues:
        return

    print(title)

    for issue in issues:
        print(
            f"- {issue.collection}[{issue.index}] "
            f"{issue.food_id}: {issue.message}"
        )

    print()


def print_collection_errors(collections: list[CollectionData]) -> None:
    """Print collection loading errors."""

    collection_errors = [
        (collection.filename, error)
        for collection in collections
        for error in collection.errors
    ]

    if not collection_errors:
        return

    print("Collection Errors")

    for filename, error in collection_errors:
        print(f"- {filename}: {error}")

    print()


def print_audit_report(
    statistics: AuditStatistics,
    manifest_result: ManifestResult,
    collections: list[CollectionData],
    schema_issues: list[ValidationIssue],
    category_issues: list[ValidationIssue],
    duplicate_ids: list[DuplicateIssue],
    duplicate_names: list[DuplicateIssue],
    verbose: bool = False,
) -> None:
    """Print the complete FoodVision knowledge-base audit report."""

    print("=" * 50)
    print("FoodVision Knowledge Base Audit")
    print("=" * 50)
    print()
    print_metric("Collections Checked:", statistics.total_collections)
    print()
    print_metric("Total Foods:", statistics.total_foods)
    print()
    print_metric("Duplicate IDs:", statistics.duplicate_ids)
    print()
    print_metric("Duplicate Display Names:", statistics.duplicate_names)
    print()
    print_metric("Schema Errors:", statistics.schema_errors)
    print()
    print_metric("Manifest Errors:", statistics.manifest_errors)
    print()
    print_metric("Collection Errors:", statistics.collection_errors)
    print()
    print_metric("Unknown Categories:", statistics.unknown_categories)
    print()
    print_metric("Foods Missing USDA:", statistics.foods_missing_usda)
    print()
    print_metric("Recognizable = False:", statistics.recognizable_false)
    print()
    print("-" * 50)
    print()
    print("Foods Per Collection")
    print()

    for collection in collections:
        print(
            f"{display_collection_name(collection.filename):<28}"
            f"{statistics.foods_per_collection[collection.filename]:>8}"
        )

    print()
    print("-" * 50)
    print()

    if verbose:
        if manifest_result.errors:
            print("Manifest Errors")

            for error in manifest_result.errors:
                print(f"- {error}")

            print()

        print_collection_errors(collections)
        print_duplicate_details("Duplicate IDs", duplicate_ids)
        print_duplicate_details("Duplicate Display Names", duplicate_names)
        print_validation_details("Schema Errors", schema_issues)
        print_validation_details("Unknown Categories", category_issues)

    print("STATUS")
    print()
    print("PASS" if audit_passed(statistics) else "FAIL")
    print()
    print("=" * 50)
