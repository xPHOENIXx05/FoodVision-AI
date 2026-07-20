"""Command-line entry point for the FoodVision knowledge-base auditor."""

from __future__ import annotations

import argparse
from pathlib import Path

from duplicate_checker import find_duplicates
from manifest_checker import check_manifest
from report import print_audit_report
from schema_checker import load_collections, validate_collections
from statistics import audit_passed, build_statistics


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the knowledge-base auditor."""

    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Audit the FoodVision knowledge base."
    )
    parser.add_argument(
        "--knowledge-base-dir",
        type=Path,
        default=project_root / "data" / "knowledge_base",
        help="Path to the FoodVision knowledge_base directory.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed validation errors.",
    )
    return parser.parse_args()


def run_audit(knowledge_base_dir: Path, verbose: bool = False) -> bool:
    """Run the read-only knowledge-base audit."""

    manifest_result = check_manifest(knowledge_base_dir)
    collections = load_collections(
        knowledge_base_dir,
        manifest_result.collections,
    )
    schema_issues, category_issues = validate_collections(collections)
    duplicate_ids, duplicate_names = find_duplicates(collections)
    statistics = build_statistics(
        manifest_result=manifest_result,
        collections=collections,
        schema_issues=schema_issues,
        category_issues=category_issues,
        duplicate_ids=duplicate_ids,
        duplicate_names=duplicate_names,
    )

    print_audit_report(
        statistics=statistics,
        manifest_result=manifest_result,
        collections=collections,
        schema_issues=schema_issues,
        category_issues=category_issues,
        duplicate_ids=duplicate_ids,
        duplicate_names=duplicate_names,
        verbose=verbose,
    )

    return audit_passed(statistics)


if __name__ == "__main__":
    args = parse_args()
    run_audit(
        knowledge_base_dir=args.knowledge_base_dir,
        verbose=args.verbose,
    )
