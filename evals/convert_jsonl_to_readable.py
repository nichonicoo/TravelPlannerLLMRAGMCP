from pathlib import Path
import json
import asyncio
import pandas as pd
from app.core.settings import settings


# =========================
# Configurable Paths
# =========================
JSONL_PATH = settings.EVALS_DIR / "5_judge" / "judge_eval.jsonl"
JSON_OUTPUT = settings.EVALS_DIR / "6_readable" / "results_pretty.json"
CSV_OUTPUT = settings.EVALS_DIR / "6_readable" / "results.csv"
EXCEL_OUTPUT = settings.EVALS_DIR / "6_readable" / "results.xlsx"


def flatten_record(record):
    row = {
        "id": record.get("id"),
        "intent": record.get("intent"),
        "question": record.get("question"),
        "winner_model": record.get("winner_model"),
        "judge_latency_sec": record.get("judge_latency_sec"),
    }

    # Vote distribution
    votes = record.get("vote_distribution", {})
    row["vote_A"] = votes.get("A")
    row["vote_B"] = votes.get("B")

    # Raw average scores
    raw_scores = record.get("raw_average_scores", {})
    for model_name, metrics in raw_scores.items():
        prefix = model_name.replace("_1_to_5", "")
        for metric_name, value in metrics.items():
            row[f"{prefix}_{metric_name}"] = value

    # Normalized metrics
    normalized = record.get("normalized_metrics", {})
    for model_name, metrics in normalized.items():
        prefix = model_name.replace("_percentages", "")
        for metric_name, value in metrics.items():
            row[f"{prefix}_{metric_name}_pct"] = value

    # Deep parse pass summaries
    passes = record.get("individual_passes", {})
    for pass_name, pass_data in passes.items():
        row[f"{pass_name}_winner"] = pass_data.get("winner")
        row[f"{pass_name}_confidence"] = pass_data.get("confidence")
        row[f"{pass_name}_reasoning"] = pass_data.get("reasoning")

        # Hallucination analysis
        hallucinations = pass_data.get("hallucination_analysis", {})
        for model_label, h_data in hallucinations.items():
            row[f"{pass_name}_hallucination_detected_{model_label}"] = h_data.get(
                "detected"
            )
            row[f"{pass_name}_hallucination_severity_{model_label}"] = h_data.get(
                "severity"
            )

    # Responses
    row["base_model_response"] = record.get("base_model_response")
    row["qlora_model_response"] = record.get("qlora_model_response")

    return row


async def jsonl_to_readable_outputs(
    jsonl_path: Path,
    json_output: Path,
    csv_output: Path,
    excel_output: Path,
):
    records = []

    # Check file exists
    if not jsonl_path.exists():
        print(f"❌ Error: File not found at {jsonl_path}")
        return

    # Read JSONL
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(
                        f"⚠️ Warning: Skipped invalid JSON on line {line_num}: {e}"
                    )

    if not records:
        print("❌ No valid records found to process.")
        return

    # Save pretty JSON
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Flatten records
    flattened = [flatten_record(r) for r in records]
    df = pd.DataFrame(flattened)

    # Save CSV
    df.to_csv(
        csv_output,
        index=False,
        encoding="utf-8-sig",
    )

    # Save Excel
    try:
        with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:
            df.to_excel(
                writer,
                sheet_name="evaluation_results",
                index=False,
            )

            # Summary sheet
            summary = {
                "total_questions": [len(df)],
                "avg_latency_sec": [
                    df["judge_latency_sec"].mean()
                    if "judge_latency_sec" in df.columns
                    else 0
                ],
            }

            summary_df = pd.DataFrame(summary)

            summary_df.to_excel(
                writer,
                sheet_name="summary",
                index=False,
            )

    except ImportError:
        print("⚠️ 'openpyxl' dependency missing.")
        print("💡 Run: pip install openpyxl")

    print(f"✅ Saved JSON:  {json_output}")
    print(f"✅ Saved CSV:   {csv_output}")
    print(f"✅ Saved Excel: {excel_output}")


async def main():
    await jsonl_to_readable_outputs(
        jsonl_path=JSONL_PATH,
        json_output=JSON_OUTPUT,
        csv_output=CSV_OUTPUT,
        excel_output=EXCEL_OUTPUT,
    )


if __name__ == "__main__":
    asyncio.run(main())
