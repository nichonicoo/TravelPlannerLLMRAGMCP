import json
import pandas as pd
from pathlib import Path


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

        # Ambil core fields dasar termasuk status, context, dan tool_result
        record = {
            "id": str(row_dict.get("id", "")).strip() if row_dict.get("id") else None,
            "intent": str(row_dict.get("intent", "")).strip() if row_dict.get("intent") else None,
            "question": str(row_dict.get("question", "")).strip() if row_dict.get("question") else None,
            "params": {},
            "status": row_dict.get("status"),
            "context": row_dict.get("context"),
            "tool_result": row_dict.get("tool_result"),
        }

        # Jika tool_result di Excel berupa string berformat JSON, pastikan saat di-export ke JSON murni,
        # kita simpan sesuai format aslinya (bisa berupa string JSON lagi agar konsisten dengan data awal Anda)
        if isinstance(record["tool_result"], str):
            try:
                # Validasi apakah ini string JSON yang valid
                json.loads(record["tool_result"])
            except Exception:
                pass  # Jika bukan JSON valid, biarkan sebagai string biasa

        # Memasukkan semua kolom berawalan param_ ke dalam objek params
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
        # Ambil kolom utama termasuk status dan context
        flat_item = {
            "id": item.get("id"),
            "intent": item.get("intent"),
            "question": item.get("question"),
            "status": item.get("status"),
            "context": item.get("context"),
        }

        # Flatten nested params back into 'param_*' columns
        tool_res = item.get("tool_result")
        if tool_res:
            if isinstance(tool_res, str):
                try:
                    # Jika berupa string JSON, kita parse lalu dump lagi dengan indentasi
                    parsed_tool = json.loads(tool_res)
                    flat_item["tool_result"] = json.dumps(
                        parsed_tool, indent=2, ensure_ascii=False)
                except Exception:
                    flat_item["tool_result"] = tool_res
            else:
                # Jika kebetulan sudah berupa dict/list dari sistem
                flat_item["tool_result"] = json.dumps(
                    tool_res, indent=2, ensure_ascii=False)
        else:
            flat_item["tool_result"] = None

        # Flatten nested params menjadi kolom 'param_*'
        params = item.get("params", {})
        if isinstance(params, dict):
            for p_key, p_val in params.items():
                if hasattr(p_val, "strftime"):
                    p_val = p_val.strftime("%Y-%m-%d")
                flat_item[f"param_{p_key}"] = p_val

        flat_records.append(flat_item)

    df = pd.DataFrame(flat_records)

    # Urutan kolom di Excel: id, intent, question, status, context, tool_result, lalu param_*
    core_cols = ["id", "intent", "question",
                 "status", "context", "tool_result"]
    param_cols = [col for col in df.columns if col.startswith("param_")]
    ordered_columns = core_cols + sorted(param_cols)

    # Reindex dataframe
    df = df.reindex(columns=ordered_columns)

    # Simpan ke Excel
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
