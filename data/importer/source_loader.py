from pathlib import Path

from sources.csv_source import load_csv
from sources.json_source import load_json


def load_source(path):
    """
    Load data from a supported source file based on its extension.
    """

    extension = Path(path).suffix.lower()

    if extension == ".csv":
        return load_csv(path)

    if extension == ".json":
        return load_json(path)

    raise ValueError(f"Unsupported file type: {extension}")
