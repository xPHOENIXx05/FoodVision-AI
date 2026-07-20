"""One-time migration from legacy FoodVision KB records to current schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from migration_report import MigrationStats, print_migration_report
from migration_utils import (
    MANIFEST_FILE,
    SUPPORTED_CATEGORY_SET,
    build_final_manifest,
    canonical_json,
    collection_payload,
    deduplicate_foods,
    load_collection,
    load_manifest,
    migrate_food,
    new_collection_payload,
    validate_migrated_collections,
    write_collection,
    write_if_changed,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the migration."""

    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Migrate FoodVision knowledge-base records to v2 schema."
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
        help="Run migration checks and report changes without writing files.",
    )
    return parser.parse_args()


def migrate_knowledge_base(
    knowledge_base_dir: Path,
    dry_run: bool = False,
) -> MigrationStats:
    """Run the one-time v1-to-v2 migration."""

    stats = MigrationStats()
    manifest = load_manifest(knowledge_base_dir)
    collection_filenames = manifest["collections"]
    collection_files = [
        load_collection(knowledge_base_dir, filename)
        for filename in collection_filenames
    ]
    collection_lookup = {
        collection.filename: collection
        for collection in collection_files
    }
    candidates = []

    for collection in collection_files:
        for food in collection.foods:
            if not isinstance(food, dict):
                raise ValueError(
                    f"Cannot migrate non-object food in {collection.filename}"
                )

            target_filename, migrated_food = migrate_food(
                food=food,
                source_filename=collection.filename,
                stats=stats,
            )
            candidates.append((target_filename, migrated_food))

    grouped_foods = deduplicate_foods(candidates, stats)
    validate_migrated_collections(grouped_foods)
    final_manifest, removed_collections = build_final_manifest(
        manifest,
        grouped_foods,
    )

    stats.collections_removed = len(removed_collections)
    stats.manifest_updated = (
        canonical_json(final_manifest) != canonical_json(manifest)
    )

    for filename in final_manifest["collections"]:
        category = Path(filename).stem

        if category not in SUPPORTED_CATEGORY_SET:
            continue

        foods = grouped_foods.get(filename, [])
        collection = collection_lookup.get(filename)

        if collection is None:
            final_payload = new_collection_payload(foods)
            original_payload = None
        else:
            final_payload = collection_payload(collection, foods)
            original_payload = collection.payload

        if canonical_json(final_payload) != canonical_json(original_payload):
            stats.collections_updated += 1

        if not dry_run:
            write_if_changed(
                knowledge_base_dir / filename,
                final_payload,
                original_payload,
            )

    if not dry_run and stats.manifest_updated:
        write_collection(knowledge_base_dir / MANIFEST_FILE, final_manifest)

    if not dry_run:
        for filename in removed_collections:
            path = knowledge_base_dir / filename

            if path.exists():
                path.unlink()

    print_migration_report(stats, dry_run=dry_run)
    return stats


if __name__ == "__main__":
    args = parse_args()
    migrate_knowledge_base(
        knowledge_base_dir=args.knowledge_base_dir,
        dry_run=args.dry_run,
    )
