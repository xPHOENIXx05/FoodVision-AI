"""Duplicate detection for the FoodVision knowledge base auditor."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from schema_checker import CollectionData


@dataclass(frozen=True)
class DuplicateIssue:
    """A duplicated field value and every place it appears."""

    value: str
    locations: list[str]


def format_location(collection: str, index: int) -> str:
    """Return a deterministic food location string."""

    return f"{collection}[{index}]"


def find_duplicates(
    collections: list[CollectionData],
) -> tuple[list[DuplicateIssue], list[DuplicateIssue]]:
    """Find duplicate ids and display names across all collections."""

    ids: dict[str, list[str]] = defaultdict(list)
    display_names: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for collection in collections:
        for index, food in enumerate(collection.foods):
            if not isinstance(food, dict):
                continue

            location = format_location(collection.filename, index)
            food_id = food.get("id")
            display_name = food.get("display_name")

            if isinstance(food_id, str) and food_id.strip():
                ids[food_id].append(location)

            if isinstance(display_name, str) and display_name.strip():
                key = display_name.casefold()
                display_names[key].append((display_name, location))

    duplicate_ids = [
        DuplicateIssue(
            value=value,
            locations=locations,
        )
        for value, locations in sorted(ids.items())
        if len(locations) > 1
    ]
    duplicate_names = [
        DuplicateIssue(
            value=sorted({display_name for display_name, _ in entries})[0],
            locations=[location for _, location in entries],
        )
        for _, entries in sorted(display_names.items())
        if len(entries) > 1
    ]

    return duplicate_ids, duplicate_names
