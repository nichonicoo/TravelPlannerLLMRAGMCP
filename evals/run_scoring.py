import asyncio
import json
import time
from datetime import datetime

from app.core.settings import settings
from app.infrastructure.llm.llm_factory import create_llm_provider

from evals.prompts import EVAL_PROMPT

from evals.utils_scoring import (
    MAX_CONTEXT_CHARS,
    MAX_TOOL_CHARS,
    apply_hallucination_penalty,
    compute_weighted_score,
    determine_winner,
    extract_json,
    is_success,
    load_jsonl,
    safe_text,
    scale_to_percentage,
    truncate_text,
    validate_pair,
    validate_scores,
)


async def run_single_judge(
    llm,
    prompt: str,
) -> dict:
    """
    Executes single independent evaluation.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "Anda adalah evaluator independen benchmark LLM. "
                "Output wajib valid JSON."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    raw_response = await llm.generate(messages)

    cleaned = extract_json(raw_response)

    return json.loads(cleaned)


async def evaluate_single_response(
    llm,
    sample: dict,
    answer: str,
) -> dict:
    """
    Evaluates one answer independently.
    """

    context = truncate_text(
        safe_text(sample.get("context")),
        MAX_CONTEXT_CHARS,
    )

    tool_result = truncate_text(
        safe_text(sample.get("tool_result")),
        MAX_TOOL_CHARS,
    )

    prompt = EVAL_PROMPT.format(
        intent=sample["intent"],
        question=sample["question"],
        context=context,
        tool_result=tool_result,
        answer=answer,
    )

    result = await run_single_judge(
        llm,
        prompt,
    )

    validate_scores(result["scores"])

    return result


async def main():

    RUN_A = settings.EVALS_DIR / "4_runs/base.jsonl"
    RUN_B = settings.EVALS_DIR / "4_runs/qlora.jsonl"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    OUTPUT_FILE = (
        settings.EVALS_DIR
        / "5_judge"
        / f"judge_eval_{timestamp}.jsonl"
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_a = load_jsonl(RUN_A)
    run_b = load_jsonl(RUN_B)

    llm = create_llm_provider()

    all_record_ids = sorted(
        set(run_a.keys()) & set(run_b.keys())
    )

    print(
        f"[*] Total evaluations scheduled: "
        f"{len(all_record_ids)}"
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as outfile:

        for idx, record_id in enumerate(
            all_record_ids,
            start=1,
        ):

            print(
                f"[{idx}/{len(all_record_ids)}] "
                f"Evaluating: {record_id}"
            )

            a = run_a[record_id]
            b = run_b[record_id]

            validate_pair(
                a,
                b,
                record_id,
            )

            if (
                not is_success(a)
                or not is_success(b)
            ):
                print(
                    f"[-] Skipping {record_id} "
                    f"due to failed inference."
                )
                continue

            try:

                start_time_base = time.perf_counter()

                base_eval = await evaluate_single_response(
                    llm,
                    a,
                    a["response"],
                )

                end_time_base = time.perf_counter()
                latency_base = end_time_base - start_time_base

                start_time_qlora = time.perf_counter()

                qlora_eval = await evaluate_single_response(
                    llm,
                    a,
                    b["response"],
                )

                end_time_qlora = time.perf_counter()
                latency_qlora = end_time_qlora - start_time_qlora

                base_score = compute_weighted_score(
                    base_eval["scores"]
                )

                qlora_score = compute_weighted_score(
                    qlora_eval["scores"]
                )

                base_score = apply_hallucination_penalty(
                    base_score,
                    base_eval.get(
                        "hallucination",
                        {},
                    ),
                )

                qlora_score = apply_hallucination_penalty(
                    qlora_score,
                    qlora_eval.get(
                        "hallucination",
                        {},
                    ),
                )

                winner, delta = determine_winner(
                    base_score,
                    qlora_score,
                )

                result = {
                    "id": record_id,

                    "intent": a["intent"],
                    "question": a["question"],

                    "winner_model": winner,

                    "base_score_raw": base_score,
                    "qlora_score_raw": qlora_score,

                    "base_score_percent": (
                        scale_to_percentage(
                            base_score
                        )
                    ),

                    "qlora_score_percent": (
                        scale_to_percentage(
                            qlora_score
                        )
                    ),

                    "score_delta": round(
                        delta,
                        3,
                    ),

                    "base_metrics": (
                        base_eval["scores"]
                    ),

                    "qlora_metrics": (
                        qlora_eval["scores"]
                    ),

                    "base_hallucination": (
                        base_eval.get(
                            "hallucination",
                            {},
                        )
                    ),

                    "qlora_hallucination": (
                        qlora_eval.get(
                            "hallucination",
                            {},
                        )
                    ),

                    "base_reasoning": (
                        base_eval.get(
                            "reasoning",
                            "",
                        )
                    ),

                    "qlora_reasoning": (
                        qlora_eval.get(
                            "reasoning",
                            "",
                        )
                    ),

                    "base_model_response": (
                        a["response"]
                    ),

                    "qlora_model_response": (
                        b["response"]
                    ),

                    "judge_latency_sec_base": round(
                        latency_base,
                        3,
                    ),

                    "judge_latency_sec_qlora": round(
                        latency_qlora,
                        3,
                    ),
                }

            except Exception as e:

                result = {
                    "id": record_id,
                    "intent": a["intent"],
                    "judge_error": str(e),
                }

            outfile.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("\n[+] Evaluation complete.")
    print(
        f"[+] Output file: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    asyncio.run(main())
