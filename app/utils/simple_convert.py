from pathlib import Path
from app.utils.file_converter import (
    import_excel_to_json,
    export_json_to_excel,
    json_to_jsonl,
    jsonl_to_json,
)

def main():
    # -------------------------------------------------------------------------
    # 1. DEFINE YOUR PATHS HERE
    # -------------------------------------------------------------------------
    # You can use absolute paths or relative paths (e.g., Path("data/input.xlsx"))
    INPUT_PATH = Path("evals/1_inputs/excel/test_dataset.xlsx")
    OUTPUT_PATH = Path("evals/1_inputs/excel/test_dataset.json")
    
    
    # -------------------------------------------------------------------------
    # 2. UNCOMMENT THE ONLY ONE YOU WANT TO RUN
    # -------------------------------------------------------------------------
    print(f"🚀 Running conversion from '{INPUT_PATH}' to '{OUTPUT_PATH}'...")

    # --- Excel <-> JSON ---
    import_excel_to_json(INPUT_PATH, OUTPUT_PATH)
    # export_json_to_excel(INPUT_PATH, OUTPUT_PATH)

    # --- JSON <-> JSONL ---
    # json_to_jsonl(INPUT_PATH, OUTPUT_PATH)
    # jsonl_to_json(INPUT_PATH, OUTPUT_PATH)

    
    print("✨ Done!")

if __name__ == "__main__":
    main()
