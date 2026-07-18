def print_collection_report(
    collection_name,
    csv_file,
    output_file,
    rows_read,
    imported,
    invalid=0,
    duplicates=0,
):
    """
    Print a summary report for a single imported collection.
    """

    print("\n" + "=" * 50)
    print("FoodVision AI Import Report")
    print("=" * 50)

    print(f"Collection : {collection_name}")
    print(f"CSV File   : {csv_file}")
    print(f"Output     : {output_file}")

    print()

    print(f"Rows Read  : {rows_read}")
    print(f"Imported   : {imported}")
    print(f"Invalid    : {invalid}")
    print(f"Duplicates : {duplicates}")

    print()

    print("Status     : SUCCESS")
    print("=" * 50)
    
def print_import_summary(results):
    """
    Print a summary after all collections have been imported.

    results = [
        ("fruits", 247),
        ("vegetables", 198),
    ]
    """

    print("\n" + "=" * 50)
    print("FoodVision AI Import Summary")
    print("=" * 50)

    total = 0

    for name, count in results:
        print(f"✓ {name.title():<20} {count}")
        total += count

    print("\n" + "-" * 50)
    print(f"Collections : {len(results)}")
    print(f"Total Foods : {total}")
    print("\nStatus      : SUCCESS")
    print("=" * 50)