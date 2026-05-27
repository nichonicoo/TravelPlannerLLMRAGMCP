import json
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

WEIGHTS = {
    "correctness": 0.30,
    "groundedness": 0.30,
    "completeness": 0.20,
    "clarity": 0.10,
    "helpfulness": 0.10,
}

TIE_THRESHOLD = 0.20


def load_jsonl(path: Path) -> dict:
    """
    Loads JSONL file into dictionary keyed by record id.
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
                    f"Duplicate ID detected: {record_id}"
                )

            data[record_id] = item

    return data


def validate_pair(a: dict, b: dict, record_id: str):
    """
    Ensures both compared records represent same task.
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
            f"Mismatched: {', '.join(mismatches)}"
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

    return text[:limit] + "\n...[TRUNCATED]..."


def extract_json(text: str) -> str:
    """
    Robust JSON extraction from model outputs.
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text.split("```json", 1)[1]

    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object found in model output."
        )

    return text[start:end + 1]


def validate_scores(scores: dict):
    """
    Validates rubric score schema integrity.
    """

    if not isinstance(scores, dict):
        raise ValueError("Scores must be a dictionary.")

    for dim in DIMENSIONS:

        if dim not in scores:
            raise ValueError(
                f"Missing dimension: {dim}"
            )

        value = scores[dim]

        try:
            numeric = int(value)

        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid score for {dim}: {value}"
            )

        if numeric < 1 or numeric > 5:
            raise ValueError(
                f"Out-of-range score for {dim}: {numeric}"
            )


def compute_weighted_score(scores: dict) -> float:
    """
    Computes weighted aggregate rubric score.
    """

    total = 0.0

    for dim, weight in WEIGHTS.items():
        total += float(scores[dim]) * weight

    return round(total, 3)


def apply_hallucination_penalty(
    score: float,
    hallucination: dict,
) -> float:
    """
    Applies penalties for hallucinated content.
    """

    if hallucination.get("detected"):

        severity = int(
            hallucination.get("severity", 0)
        )

        penalties = {
            0: 0.0,
            1: 0.25,
            2: 0.75,
            3: 1.50,
        }

        score -= penalties.get(severity, 0)

    return round(max(score, 1.0), 3)


def scale_to_percentage(score_1_to_5: float) -> float:
    """
    Converts 1-5 scale into percentage.
    """

    score = max(1.0, min(5.0, float(score_1_to_5)))

    return round(
        ((score - 1.0) / 4.0) * 100,
        2,
    )


def determine_winner(
    base_score: float,
    qlora_score: float,
) -> tuple[str, float]:
    """
    Determines winner using tie threshold.
    """

    delta = abs(base_score - qlora_score)

    if delta <= TIE_THRESHOLD:
        return "TIE", delta

    if base_score > qlora_score:
        return "BASE", delta

    return "QLORA", delta


def is_success(item: dict) -> bool:
    """
    Normalizes operational success detection.
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
