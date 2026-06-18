import argparse
import asyncio
import json
import time

from langfuse import observe

from app.core.settings import settings, langfuse
from evals.judges import BaseJudge, JudgeFactory
from evals.utils_scoring import (
    apply_hallucination_penalty,
    compute_weighted_score,
    determine_winner,
    is_success,
    load_jsonl,
    safe_text,
    scale_to_percentage,
    validate_pair,
    validate_scores,
)


@observe(name="judge-evaluation", as_type="generation")
async def evaluate_single_response(
    judge: BaseJudge,
    sample: dict,
    answer: str,
    model_run_type: str,  # "base" or "qlora"
    judge_name: str
) -> tuple[dict, float]:
    """Evaluates one answer independently and logs the process to Langfuse."""

    intent = sample.get("intent", "LLM")

    raw_context = sample.get("context")
    raw_tool = sample.get("tool_result")

    reference_blocks = []

    if sample.get("context") not in [None, "null", "", "None"]:
        reference_blocks.append(f"=== KONTEKS ===\n{safe_text(raw_context)}")

    if sample.get("tool_result") not in [None, "null", "", "None"]:
        reference_blocks.append(f"=== HASIL EKSEKUSI TOOL ===\n{safe_text(raw_tool)}")

    if not reference_blocks:
        if sample.get("intent") == "LLM":
            reference_data = "Tidak membutuhkan data eksternal (Intent: LLM). Evaluasi groundedness berdasarkan fakta umum dunia nyata."
        else:
            reference_data = "Tidak ada data pendukung yang tersedia dari sistem backend."
    else:
        reference_data = "\n\n".join(reference_blocks)

    from evals.prompts import SYSTEM_EVAL_PROMPT, USER_EVAL_PROMPT

    user_prompt = USER_EVAL_PROMPT.format(
        intent=intent,
        question=sample["question"],
        reference=reference_data,
        answer=answer,
    )

    start_time = time.perf_counter()

    result = await judge.evaluate(
        system_prompt=SYSTEM_EVAL_PROMPT,
        user_prompt=user_prompt
    )
    validate_scores(result["scores"])

    latency = time.perf_counter() - start_time

    return result, latency


async def main():
    # Set up argument parsing to easily switch backends
    parser = argparse.ArgumentParser(
        description="Run LLM-as-a-Judge evaluation.")
    parser.add_argument(
        "--judge",
        type=str,
        default="gemini",
        choices=["gemini", "deepseek"],
        help="Specify which LLM judge platform to execute scoring."
    )
    args = parser.parse_args()

    RUN_A = settings.EVALS_DIR / "4_runs/base.jsonl"
    RUN_B = settings.EVALS_DIR / "4_runs/qlora.jsonl"

    # Dynamic output naming based on the judge type chosen
    OUTPUT_FILE = settings.EVALS_DIR / "5_judge" / \
        f"judge_eval_{args.judge}.jsonl"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_a = load_jsonl(RUN_A)
    run_b = load_jsonl(RUN_B)

    # Instantiate the concrete implementation seamlessly using our Factory
    print(
        f"[*] Initializing factory engine for judge target: {args.judge.upper()}")
    judge = JudgeFactory.create_judge(args.judge)

    all_record_ids = sorted(set(run_a.keys()) & set(run_b.keys()))
    print(f"[*] Total evaluations scheduled: {len(all_record_ids)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        for idx, record_id in enumerate(all_record_ids, start=1):
            print(f"[{idx}/{len(all_record_ids)}] Evaluating: {record_id}")

            a = run_a[record_id]
            b = run_b[record_id]

            validate_pair(a, b, record_id)

            if not is_success(a) or not is_success(b):
                print(f"[-] Skipping {record_id} due to failed inference.")
                continue

            try:
                # --- Evaluate Base Model ---
                base_eval, judge_latency_base = await evaluate_single_response(
                    judge=judge,
                    sample=a,
                    answer=a["response"],
                    model_run_type="base",
                    judge_name=args.judge
                )

                # --- Evaluate QLoRA Model ---
                qlora_eval, judge_latency_qlora = await evaluate_single_response(
                    judge=judge,
                    sample=a,
                    answer=b["response"],
                    model_run_type="qlora",
                    judge_name=args.judge
                )

                # --- Metric Parsing and Math ---
                base_score = compute_weighted_score(base_eval["scores"])
                qlora_score = compute_weighted_score(qlora_eval["scores"])

                base_score = apply_hallucination_penalty(
                    base_score, base_eval.get("hallucination", {})
                )
                qlora_score = apply_hallucination_penalty(
                    qlora_score, qlora_eval.get("hallucination", {})
                )

                winner, delta = determine_winner(base_score, qlora_score)

                result = {
                    "id": record_id,
                    "intent": a["intent"],
                    "question": a["question"],
                    "winner_model": winner,
                    "base_score_raw": base_score,
                    "qlora_score_raw": qlora_score,
                    "base_score_percent": scale_to_percentage(base_score),
                    "qlora_score_percent": scale_to_percentage(qlora_score),
                    "score_delta": round(delta, 3),
                    "base_metrics": base_eval["scores"],
                    "qlora_metrics": qlora_eval["scores"],
                    "base_hallucination": base_eval.get("hallucination", {}),
                    "qlora_hallucination": qlora_eval.get("hallucination", {}),
                    "base_reasoning": base_eval.get("reasoning", ""),
                    "qlora_reasoning": qlora_eval.get("reasoning", ""),
                    "base_model_response": a["response"],
                    "qlora_model_response": b["response"],
                    "judge_latency_sec_base": round(judge_latency_base, 3),
                    "judge_latency_sec_qlora": round(judge_latency_qlora, 3),
                }

            except Exception as e:
                result = {
                    "id": record_id,
                    "intent": a["intent"],
                    "judge_error": str(e),
                }

            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

            # Rate limit backoff delay per row
            await asyncio.sleep(30)

    print(f"\n[+] Evaluation complete.\n[+] Output file: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
