from report import print_collection_report

print_collection_report(
    collection_name="fruits",
    csv_file="fruits.csv",
    output_file="fruits.json",
    rows_read=10,
    imported=10,
    invalid=0,
    duplicates=0,
)