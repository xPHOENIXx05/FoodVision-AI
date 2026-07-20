"""Manifest validation for the FoodVision knowledge base auditor."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_MANIFEST_FIELDS = (
    "schema_version",
    "collections",
)


@dataclass(frozen=True)
class ManifestResult:
    """Result of validating knowledge_base/manifest.json."""

    manifest_path: Path
    collections: list[str]
    errors: list[str]


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    """Load JSON from a path and return any parsing errors."""

    if not path.exists():
        return None, [f"Manifest file not found: {path}"]

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), []
    except json.JSONDecodeError as exc:
        return None, [f"Invalid manifest JSON: {exc}"]


def check_manifest(knowledge_base_dir: Path) -> ManifestResult:
    """Validate manifest.json and return referenced collection filenames."""

    manifest_path = knowledge_base_dir / "manifest.json"
    manifest, errors = load_json(manifest_path)

    if manifest is None:
        return ManifestResult(
            manifest_path=manifest_path,
            collections=[],
            errors=errors,
        )

    if not isinstance(manifest, dict):
        return ManifestResult(
            manifest_path=manifest_path,
            collections=[],
            errors=errors + ["Manifest must be a JSON object"],
        )

    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"Manifest missing required field: {field}")

    collections = manifest.get("collections")

    if not isinstance(collections, list):
        errors.append("Manifest field 'collections' must be a list")
        return ManifestResult(
            manifest_path=manifest_path,
            collections=[],
            errors=errors,
        )

    valid_collections: list[str] = []

    for index, collection in enumerate(collections):
        if not isinstance(collection, str) or not collection.strip():
            errors.append(
                f"Manifest collections[{index}] must be a non-empty string"
            )
            continue

        filename = collection.strip()
        valid_collections.append(filename)

        if not (knowledge_base_dir / filename).exists():
            errors.append(f"Collection file not found: {filename}")

    counts = Counter(valid_collections)

    for filename in sorted(name for name, count in counts.items() if count > 1):
        errors.append(f"Duplicate collection entry in manifest: {filename}")

    return ManifestResult(
        manifest_path=manifest_path,
        collections=valid_collections,
        errors=errors,
    )
