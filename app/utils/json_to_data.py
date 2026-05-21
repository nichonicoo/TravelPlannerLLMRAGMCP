from datetime import datetime
from app.core.settings import settings
from app.utils.file_converter import export_json_to_excel, json_to_jsonl


def main():
    dataset_name = "test_dataset"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Paths
    source_json = settings.EVALS_DIR / \
        "1_inputs" / "json" / f"{dataset_name}.json"
    output_excel = settings.EVALS_DIR / \
        "2_processed" / "excel" / f"{dataset_name}_{timestamp}.xlsx"
    output_jsonl = settings.EVALS_DIR / \
        "2_processed" / "jsonl" / f"{dataset_name}_{timestamp}.jsonl"

    # Ensure output folders exist
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    if not source_json.exists():
        print(f"❌ Error: Master JSON not found at {source_json}")
        return

    # Step 1: Master JSON -> Backup Excel Log
    print(f"📊 Exporting Master JSON -> Reference Excel Log...")
    export_json_to_excel(source_json, output_excel)

    # Step 2: Master JSON -> Production JSONL
    print(f"📜 Compiling Master JSON -> Production JSONL...")
    json_to_jsonl(source_json, output_jsonl)

    print(f"✨ Success! Data pipeline refreshed from Git Master JSON.")


if __name__ == "__main__":
    main()
