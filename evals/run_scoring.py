import asyncio
import json
import time
from collections import Counter
from datetime import datetime

from app.core.settings import settings
from app.infrastructure.llm.llm_factory import create_llm_provider
from evals.prompts import EVAL_PROMPT
from evals.utils_scoring import (
    MAX_CONTEXT_CHARS,
    MAX_TOOL_CHARS,
    average_scores,
    extract_json,
    is_success,
    load_jsonl,
    normalize_winner,
    remap_scores,
    safe_text,
    scale_to_percentage,
    truncate_text,
    determine_consensus_winner,
    validate_pair,
    validate_scores,
)


async def run_single_judge(llm, prompt: str) -> dict:
    """Executes call payload against designated independent evaluator engine."""
    messages = [
        {
            "role": "system",
            "content": "Anda adalah mesin evaluator ilmiah independen. Output Anda wajib berupa format valid JSON sesuai skema kaku yang diminta.",
        },
        {"role": "user", "content": prompt},
    ]
    raw_response = await llm.generate(messages)
    cleaned = extract_json(raw_response)
    return json.loads(cleaned)


async def evaluate_direction(llm, sample: dict, answer_a: str, answer_b: str) -> dict:
    """Prepares structured prompt strings with safely bounded character limits."""
    context = truncate_text(
        safe_text(sample.get("context")), MAX_CONTEXT_CHARS
    )
    tool_result = truncate_text(
        safe_text(sample.get("tool_result")), MAX_TOOL_CHARS
    )

    prompt = EVAL_PROMPT.format(
        intent=sample["intent"],
        question=sample["question"],
        context=context,
        tool_result=tool_result,
        answer_a=answer_a,
        answer_b=answer_b,
    )
    return await run_single_judge(llm, prompt)


async def main():
    RUN_A = settings.EVALS_DIR / "4_runs/base.jsonl"
    RUN_B = settings.EVALS_DIR / "4_runs/qlora.jsonl"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILE = (
        settings.EVALS_DIR / "5_judge" / f"judge_eval_{timestamp}.jsonl"
    )
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_a = load_jsonl(RUN_A)
    run_b = load_jsonl(RUN_B)

    llm = create_llm_provider()
    
    # Intersects shared native string record indices ("q1", "q2", etc.)
    all_record_ids = sorted(set(run_a.keys()) & set(run_b.keys()))

    print(f"[*] Total comparative evaluations scheduled: {len(all_record_ids)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        for idx, record_id in enumerate(all_record_ids, start=1):
            print(f"[{idx}/{len(all_record_ids)}] Processing validation: {record_id}")

            a = run_a[record_id]
            b = run_b[record_id]
            validate_pair(a, b, record_id)

            if not is_success(a) or not is_success(b):
                print(f"[-] Skipping entry {record_id} due to operational failure statuses.")
                continue

            try:
                start_time = time.perf_counter()

                # Pass 1: Canonical Setup (A = Base, B = QLoRA)
                result_ab = await evaluate_direction(
                    llm, a, a["response"], b["response"]
                )

                # Pass 2: Inverted Swap Setup (A = QLoRA, B = Base)
                result_ba = await evaluate_direction(
                    llm, a, b["response"], a["response"]
                )

                latency = time.perf_counter() - start_time

                validate_scores(result_ab["scores"])
                validate_scores(result_ba["scores"])

                normalized_ab_winner = normalize_winner(
                    result_ab.get("winner"),
                    swapped=False,
                )

                normalized_ba_winner = normalize_winner(
                    result_ba.get("winner"),
                    swapped=True,
                )

                normalized_ba_scores = remap_scores(
                    result_ba.get("scores", {})
                )

                votes = [
                    normalized_ab_winner,
                    normalized_ba_winner,
                ]

                vote_counter = Counter(votes)

                final_winner = determine_consensus_winner(votes)

                avg_scores = {
                    "A": average_scores(
                        [
                            {"scores": result_ab.get("scores", {})},
                            {"scores": normalized_ba_scores},
                        ],
                        "A",
                    ),
                    "B": average_scores(
                        [
                            {"scores": result_ab.get("scores", {})},
                            {"scores": normalized_ba_scores},
                        ],
                        "B",
                    ),
                }

                # Explicitly label metrics with domain models to safeguard analysis
                metrics_summary = {
                    "base_model_percentages": {
                        k: scale_to_percentage(v)
                        for k, v in avg_scores["A"].items()
                        if v is not None
                    },
                    "qlora_model_percentages": {
                        k: scale_to_percentage(v)
                        for k, v in avg_scores["B"].items()
                        if v is not None
                    },
                }

                if final_winner == "A":
                    final_model_winner = "BASE"
                elif final_winner == "B":
                    final_model_winner = "QLORA"
                else:
                    final_model_winner = "TIE"

                result = {
                    "id": record_id,  # Keeps original "q1", "q2" notation completely clean
                    "intent": a["intent"],
                    "question": a["question"],
                    "winner_model": final_model_winner,
                    "vote_distribution": dict(vote_counter),
                    "raw_average_scores": {
                        "base_model_1_to_5": avg_scores["A"],
                        "qlora_model_1_to_5": avg_scores["B"],
                    },
                    "normalized_metrics": metrics_summary,
                    "individual_passes": {
                        "pass_1_base_first": result_ab,
                        "pass_2_qlora_first": result_ba,
                    },
                    "base_model_response": a["response"],
                    "qlora_model_response": b["response"],
                    "judge_latency_sec": round(latency, 3),
                }

            except Exception as e:
                result = {
                    "id": record_id,
                    "intent": a["intent"],
                    "judge_error": f"Internal execution crash: {str(e)}",
                }

            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

    print("\n[+] Evaluation sequence complete.")
    print(f"[+] Output log file located at: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
