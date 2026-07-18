from pathlib import Path

from normalizer import normalize_name
from deduplicator import remove_duplicate_names
from sources.csv_source import load_csv
from schema_mapper import map_to_schema
from writer import write_collection
from config import load_collections
from validator import validate_food
from collection_validator import validate_collection
from report import print_collection_report
from report import (
    print_collection_report,
    print_import_summary,
)

results = []

def import_csv(csv_path, category, food_type):  
    rows = load_csv(csv_path)
    # Normalize names
    for row in rows:
        row["name"] = normalize_name(row["name"])
        
        

    # Remove duplicates
    rows = remove_duplicate_names(rows)

    foods = []

    for row in rows:
        foods.append(
            map_to_schema(
                row,
                category=category,
                food_type=food_type
            )
        )    
       
    # Validate each food
    for food in foods:
         result = validate_food(food)

         if not result["valid"]:
            raise ValueError(
                f"Invalid food '{food['display_name']}': "
                + ", ".join(result["errors"])
            )
    
    # Validate the collection
    collection_result = validate_collection(foods)

    if not collection_result["valid"]:
        raise ValueError(
            "\n".join(collection_result["errors"])
        )

    
    return foods




if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    config_file = base_dir / "collections.json"

    collections = load_collections(config_file)

    for collection in collections:

        csv_file = (
            base_dir.parent
            / "imports"
            / collection["csv"]
        )

        foods = import_csv(
            csv_file,
            category=collection["category"],
            food_type=collection["type"]
        )
        output_file = (
            base_dir.parent
            / "knowledge_base"
            / collection["output"]
        )

        write_collection(output_file, foods)

        print_collection_report(
            collection_name=collection["category"],
            csv_file=collection["csv"],
            output_file=collection["output"],
            rows_read=len(foods),
            imported=len(foods),
            invalid=0,
            duplicates=0,
        )
        
        results.append(
    (
        collection["category"],
        len(foods),
    )
)
        print_import_summary(results)