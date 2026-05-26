import json
import re
from pathlib import Path

MAX_CONTEXT_CHARS = 8000
MAX_TOOL_CHARS = 4000

DIMENSIONS = [
    "correctness",
    "groundedness",
    "completeness",
    "clarity",
    "helpfulness",
]


def load_jsonl(path: Path) -> dict:
    """
    Loads JSONL file into dictionary keyed by native `id`.

    Raises:
        ValueError: duplicate IDs detected
        KeyError: missing id field
    """
    data = {}

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip():
                continue

            item = json.loads(line)

            if "id" not in item:
                raise KeyError(
                    f"Missing 'id' field in {path} line {line_num}"
                )

            record_id = item["id"]

            if record_id in data:
                raise ValueError(
                    f"Duplicate ID detected: {record_id} "
                    f"in {path} line {line_num}"
                )

            data[record_id] = item

    return data


def validate_pair(a: dict, b: dict, record_id: str):
    """
    Ensures both compared samples represent identical tasks.
    """

    checks = [
        ("question", a.get("question"), b.get("question")),
        ("intent", a.get("intent"), b.get("intent")),
        ("params", a.get("params"), b.get("params")),
    ]

    mismatches = []

    for field, av, bv in checks:
        if av != bv:
            mismatches.append(field)

    if mismatches:
        raise ValueError(
            f"Dataset mismatch for {record_id}. "
            f"Mismatched fields: {', '.join(mismatches)}"
        )


def safe_text(value, fallback="Tidak ada data.") -> str:
    """
    Safely converts arbitrary payloads into prompt-safe strings.
    """

    if value is None:
        return fallback

    if isinstance(value, (dict, list)):
        value = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )

    value = str(value).strip()

    return value if value else fallback


def truncate_text(text: str, limit: int) -> str:
    """
    Truncates oversized payloads safely.
    """

    if len(text) <= limit:
        return text

    return text[:limit] + "\n...[TRUNCATED IN EVAL]..."


def extract_json(text: str) -> str:
    """
    Extracts first valid JSON object from model output.
    """

    text = text.strip()

    if text.startswith("```json"):
        text = (
            text.removeprefix("```json")
            .removesuffix("```")
            .strip()
        )

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError(
            "No JSON payload block found in model output."
        )

    return match.group(0)


def scale_to_percentage(score_1_to_5: float) -> float:
    """
    Converts 1-5 scale into 0-100 percentage scale.
    """

    try:
        score = float(score_1_to_5)
        score = max(1.0, min(5.0, score))

        return round(((score - 1.0) / 4.0) * 100, 2)

    except (ValueError, TypeError):
        return 0.0


def validate_scores(scores: dict):
    """
    Validates judge score schema integrity.
    """

    for side in ["A", "B"]:
        if side not in scores:
            raise ValueError(f"Missing score side: {side}")

        if not isinstance(scores[side], dict):
            raise ValueError(
                f"Scores for side '{side}' must be a dictionary."
            )

        for dim in DIMENSIONS:
            if dim not in scores[side]:
                raise ValueError(
                    f"Missing dimension '{dim}' in side '{side}'"
                )

            value = scores[side][dim]

            if value is None:
                continue

            try:
                numeric = float(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid numeric value for "
                    f"{side}.{dim}: {value}"
                )

            if numeric < 1 or numeric > 5:
                raise ValueError(
                    f"Out-of-range score for "
                    f"{side}.{dim}: {numeric}"
                )


def average_scores(results: list, side: str) -> dict:
    """
    Averages metric layers across multiple judge passes.
    """

    averaged = {}

    for dim in DIMENSIONS:
        vals = []

        for r in results:
            try:
                val = r["scores"][side][dim]

                if val is not None:
                    vals.append(float(val))

            except (KeyError, TypeError, ValueError):
                continue

        averaged[dim] = (
            round(sum(vals) / len(vals), 2)
            if vals
            else None
        )

    return averaged


def normalize_winner(winner: str, swapped: bool) -> str:
    """
    Normalizes winner labels during swap evaluation.
    """

    if not winner:
        return "TIE"

    winner = str(winner).strip().upper()

    if winner not in {"A", "B"}:
        return "TIE"

    if not swapped:
        return winner

    return "B" if winner == "A" else "A"


def remap_scores(scores: dict) -> dict:
    """
    Swaps score orientation after inverted evaluation pass.
    """

    return {
        "A": scores.get("B", {}),
        "B": scores.get("A", {}),
    }


def determine_consensus_winner(votes: list[str]) -> str:
    """
    Requires strict agreement across passes.

    Examples:
        ["A", "A"] -> "A"
        ["B", "B"] -> "B"
        ["A", "B"] -> "TIE"
    """

    normalized = [str(v).upper() for v in votes]

    if all(v == "A" for v in normalized):
        return "A"

    if all(v == "B" for v in normalized):
        return "B"

    return "TIE"

def is_success(item: dict) -> bool:
    """
    Normalizes operational success detection across pipelines.
    """

    inference_status = str(
        item.get("inference_status", "")
    ).upper()

    status = str(
        item.get("status", "")
    ).upper()

    return (
        inference_status == "SUCCESS"
        or status in {"SUCCESS", "OK"}
    )
