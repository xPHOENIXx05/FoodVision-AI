from pathlib import Path
import json


def write_collection(output_path, foods):
    """
    Write a food collection to a JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            foods,
            f,
            indent=4,
            ensure_ascii=False
        )
