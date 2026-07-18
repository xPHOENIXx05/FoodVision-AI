from pathlib import Path

from config import load_collections

base_dir = Path(__file__).resolve().parent

config_file = base_dir / "collections.json"

collections = load_collections(config_file)

print(collections)