from datetime import datetime
from app.core.settings import settings
from app.utils.file_converter import (
    import_excel_to_json,
    export_json_to_excel,
    json_to_jsonl,
    jsonl_to_json,
)

def main():
    dataset_name = "test_dataset"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. SETUP THE PIPELINE PATHS (Matching our structured folder layout)
    input_excel_dir = settings.EVALS_DIR / "1_inputs"
    
    processed_json_dir = settings.EVALS_DIR / "2_processed" / "json"
    processed_excel_dir = settings.EVALS_DIR / "2_processed" / "excel"
    processed_jsonl_dir = settings.EVALS_DIR / "2_processed" / "jsonl"

    # Ensure all target folders exist
    processed_json_dir.mkdir(parents=True, exist_ok=True)
    processed_excel_dir.mkdir(parents=True, exist_ok=True)
    processed_jsonl_dir.mkdir(parents=True, exist_ok=True)

    # 2. DEFINING SOURCE AND GENERATED PATHS
    # Static master JSON path (No timestamp in filename!) so Git tracks changes over time
    master_json_path = processed_json_dir / f"{dataset_name}.json"
    
    # Static input Excel file path
    source_excel_path = input_excel_dir / f"{dataset_name}.xlsx"

    # Timestamped tracking files (Useful for running evaluations or debugging history)
    output_excel_path = processed_excel_dir / f"{dataset_name}_{timestamp}.xlsx"
    output_jsonl_path = processed_jsonl_dir / f"{dataset_name}_{timestamp}.jsonl"
    output_json_verification = processed_json_dir / f"{dataset_name}_{timestamp}_from_jsonl.json"


    # 3. CHOOSE WORKFLOW ROUTING LOGIC
    # Scenario A: If Excel input exists, assume it's the newer source and import it to JSON
    if source_excel_path.exists():
        print(f"📦 Excel file detected at {source_excel_path}.")
        print(f"🔄 Updating master JSON from Excel...")
        import_excel_to_json(source_excel_path, master_json_path)
    
    # Scenario B: If Excel doesn't exist but the master JSON does, we use the JSON directly
    elif master_json_path.exists():
        print(f"📂 No fresh Excel file found. Using existing Master JSON at {master_json_path} (Git Source of Truth).")
    
    else:
        print(f"❌ Error: Neither {source_excel_path} nor {master_json_path} exists!")
        return


    # 4. RUN THE DOWNSTREAM CONVERSIONS (Always runs from the updated Master JSON)
    print(f"📊 Exporting Master JSON to a timestamped Excel log for analysis...")
    export_json_to_excel(master_json_path, output_excel_path)

    print(f"📜 Compiling Master JSON -> JSONL for the RAG/MCP Flow...")
    json_to_jsonl(master_json_path, output_jsonl_path)

    print(f"🔄 Running verification check (JSONL -> JSON)...")
    jsonl_to_json(output_jsonl_path, output_json_verification)

    print(f"✨ Pipeline completed successfully! Ready for your RAG pipeline.")


if __name__ == "__main__":
    main()
