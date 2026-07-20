"""Console reporting for the FoodVision v1-to-v2 migration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MigrationStats:
    """Counters collected during the one-time knowledge-base migration."""

    collections_updated: int = 0
    foods_updated: int = 0
    categories_standardized: int = 0
    types_standardized: int = 0
    missing_fields_added: int = 0
    duplicate_foods_removed: int = 0
    collections_removed: int = 0
    ids_regenerated: int = 0
    display_names_normalized: int = 0
    usda_standardized: int = 0
    manifest_updated: bool = False


def print_metric(label: str, value: int) -> None:
    """Print one aligned migration metric."""

    print(f"{label:<28}{value:>8}")


def print_migration_report(stats: MigrationStats, dry_run: bool = False) -> None:
    """Print a concise migration summary."""

    print("=" * 40)
    print("FoodVision Migration Report")
    print("=" * 40)
    print()

    if dry_run:
        print("Mode: DRY RUN")
        print()

    print_metric("Collections Updated:", stats.collections_updated)
    print()
    print_metric("Foods Updated:", stats.foods_updated)
    print()
    print_metric("Categories Standardized:", stats.categories_standardized)
    print()
    print_metric("Types Standardized:", stats.types_standardized)
    print()
    print_metric("Missing Fields Added:", stats.missing_fields_added)
    print()
    print_metric("Duplicate Foods Removed:", stats.duplicate_foods_removed)
    print()
    print_metric("Collections Removed:", stats.collections_removed)
    print()
    print_metric("IDs Regenerated:", stats.ids_regenerated)
    print()
    print_metric("Display Names Normalized:", stats.display_names_normalized)
    print()
    print_metric("USDA Fields Standardized:", stats.usda_standardized)
    print()
    print_metric("Manifest Updated:", int(stats.manifest_updated))
    print()
    print("=" * 40)
