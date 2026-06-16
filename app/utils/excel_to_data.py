from datetime import datetime
from app.core.settings import settings
from app.utils.file_converter import import_excel_to_json, json_to_jsonl


def main():
    dataset_name = "test_dataset_50"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Paths
    source_excel = settings.EVALS_DIR / \
        "1_inputs" / "excel" / f"{dataset_name}.xlsx"
    output_json = settings.EVALS_DIR / \
        "2_processed" / "json" / f"{dataset_name}.json"
    output_jsonl = settings.EVALS_DIR / \
        "2_processed" / "jsonl" / f"{dataset_name}_{timestamp}.jsonl"

    # Ensure output folders exist
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    if not source_excel.exists():
        print(f"❌ Error: Excel source not found at {source_excel}")
        return

    # Step 1: Excel -> Master JSON
    print(f"📦 Importing Excel sheet -> Git Master JSON...")
    import_excel_to_json(source_excel, output_json)

    # Step 2: Master JSON -> Production JSONL
    print(f"📜 Compiling Git Master JSON -> Production JSONL...")
    json_to_jsonl(output_json, output_jsonl)

    print(f"✨ Success! Data pipeline refreshed from Excel source.")


if __name__ == "__main__":
    main()
