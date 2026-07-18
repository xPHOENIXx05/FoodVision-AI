from pathlib import Path

from sources.csv_source import load_csv

BASE_DIR = Path(__file__).resolve().parent
csv_file = BASE_DIR.parent / "imports" / "fruits.csv"

rows = load_csv(csv_file)

print(rows)