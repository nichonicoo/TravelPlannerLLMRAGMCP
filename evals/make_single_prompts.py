import json
from pathlib import Path
from evals.prompts import USER_EVAL_PROMPT

def safe_text(value):
    if value is None:
        return ""
    return str(value)


def load_record(jsonl_path: str, record_id: str | None = None):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            if record_id is None:
                return row

            if row.get("id") == record_id:
                return row

    raise ValueError(
        f"Record ID '{record_id}' not found in {jsonl_path}"
    )

EVALS_DIR = Path("./evals")
JSONL_FILE = EVALS_DIR / "4_runs/base.jsonl"
RECORD_ID = "q1"

sample = load_record(JSONL_FILE, RECORD_ID)

raw_context = sample.get("context")
raw_tool = sample.get("tool_result")

# --- Combine tool_result and context dynamically ---
reference_blocks = []

if sample.get("context") not in [None, "null", "", "None"]:
    reference_blocks.append(f"=== KONTEKS ===\n{safe_text(raw_context)}")

if sample.get("tool_result") not in [None, "null", "", "None"]:
    reference_blocks.append(f"=== HASIL EKSEKUSI TOOL ===\n{safe_text(raw_tool)}")

# Fallback if both are genuinely empty
if not reference_blocks:
    if sample.get("intent") == "LLM":
        reference_data = "Tidak membutuhkan data eksternal (Intent: LLM). Evaluasi groundedness berdasarkan fakta umum dunia nyata."
    else:
        reference_data = "Tidak ada data pendukung yang tersedia dari sistem backend."
else:
    reference_data = "\n\n".join(reference_blocks)

prompt = USER_EVAL_PROMPT.format(
    intent=safe_text(sample.get("intent")),
    question=safe_text(sample.get("question")),
    reference=reference_data,
    answer=safe_text(sample.get("response")),
)

print(prompt)
