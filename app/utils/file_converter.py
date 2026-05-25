import json
from pathlib import Path
import pandas as pd


def import_excel_to_json(excel_path: Path, json_path: Path) -> None:
    """Reads an Excel file and builds a structured JSON file.

    Top level fields: id, intent, question.
    Everything else (prefixed with 'param_') goes into the 'params' object.
    """
    df = pd.read_excel(excel_path)
    df = df.where(pd.notnull(df), None)

    structured_data = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()

        # Core top-level fields only
        record = {
            "id": str(row_dict.get("id", "")).strip(),
            "intent": str(row_dict.get("intent", "")).strip(),
            "question": str(row_dict.get("question", "")).strip(),
            "params": {},
        }

        # Replace the param loop inside import_excel_to_json with this:
        for key, value in row_dict.items():
            if key.startswith("param_") and value is not None:
                json_param_key = key.replace("param_", "", 1)

                # Handle empty/NaN/NaT values safely
                if pd.isna(value):
                    continue

                # If the column name suggests it's a date field, force it into a uniform date string
                if "date" in json_param_key.lower():
                    try:
                        # This handles BOTH real Excel dates and raw text strings like "10/09/2026"
                        parsed_date = pd.to_datetime(value)
                        value = parsed_date.strftime("%Y-%m-%d")
                    except Exception:
                        # If it's a messy string that can't be parsed, keep it as a string instead of crashing
                        value = str(value).strip()
                
                # For non-date parameters (like location, arrival, departure)
                elif isinstance(value, str):
                    value = value.strip()

                record["params"][json_param_key] = value

        structured_data.append(record)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=4, ensure_ascii=False)


def export_json_to_excel(json_path: Path, excel_path: Path) -> None:
    """Flattens structured JSON into an Excel sheet.

    Guarantees that columns follow the sequence: id, intent, question, then
    params.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    flat_records = []

    for item in json_data:
        flat_item = {
            "id": item.get("id"),
            "intent": item.get("intent"),
            "question": item.get("question"),
        }

        # Flatten nested params back into 'param_*' columns
        params = item.get("params", {})
        if isinstance(params, dict):
            for p_key, p_val in params.items():
                if hasattr(p_val, "strftime"):
                    p_val = p_val.strftime("%Y-%m-%d")
                flat_item[f"param_{p_key}"] = p_val

        flat_records.append(flat_item)

    df = pd.DataFrame(flat_records)

    # Enforce column order: id, intent, question, then all param_ columns
    core_cols = ["id", "intent", "question"]
    param_cols = [col for col in df.columns if col.startswith("param_")]
    ordered_columns = core_cols + sorted(param_cols)

    # Reindex dataframe to guarantee Excel layout matches your preference
    df = df.reindex(columns=ordered_columns)
    df.to_excel(excel_path, index=False)


def json_to_jsonl(json_path: Path, jsonl_path: Path) -> None:
    """Converts standard JSON array to line-by-line JSONL format."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def jsonl_to_json(jsonl_path: Path, json_path: Path) -> None:
    """Converts line-by-line JSONL format back to standard JSON array."""
    data = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line.strip()))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
