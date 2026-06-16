import asyncio
import json
import time
from datetime import datetime

from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.settings import settings
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

@retry(
    stop=stop_after_attempt(5),  # Retry up to 5 times
    wait=wait_exponential(multiplier=2, min=4, max=30),  # Wait 4s, 8s, 16s...
    retry=retry_if_exception_type(APIError),
    reraise=True  # If it still fails after 5 times, raise the error to the try-except block
)
async def run_single_judge_with_retry(client: genai.Client, model_name: str, prompt: str, config: types.GenerateContentConfig):
    """Wraps the actual async API call for tenancy retry compatibility."""
    return await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

async def run_single_judge(
    client: genai.Client,
    prompt: str,
) -> dict:
    """
    Executes single independent evaluation using Gemma 4 31B 
    hosted for free on Google AI Studio with automatic backoff.
    """
    config = types.GenerateContentConfig(
        system_instruction="Anda adalah evaluator independen benchmark LLM. Output wajib valid JSON.",
        response_mime_type="application/json",
        temperature=0.1,
    )

    # Use the wrapped retry function
    response = await run_single_judge_with_retry(
        client=client,
        model_name="gemma-4-31b-it",
        prompt=prompt,
        config=config
    )

    raw_response = response.text
    cleaned = extract_json(raw_response)

    return json.loads(cleaned)

# FIX 1: Changed type hint from AsyncOpenAI to genai.Client
async def evaluate_single_response(
    client: genai.Client,
    sample: dict,
    answer: str,
) -> dict:
    """
    Evaluates one answer independently.
    """
    # context = truncate_text(
    #     safe_text(sample.get("context")),
    #     MAX_CONTEXT_CHARS,
    # )

    # tool_result = truncate_text(
    #     safe_text(sample.get("tool_result")),
    #     MAX_TOOL_CHARS,
    # )
    context = safe_text(sample.get("context"))
    tool_result = safe_text(sample.get("tool_result"))

    prompt = EVAL_PROMPT.format(
        intent=sample["intent"],
        question=sample["question"],
        context=context,
        tool_result=tool_result,
        answer=answer,
    )

    result = await run_single_judge(client, prompt)
    validate_scores(result["scores"])
    return result

async def main():
    RUN_A = settings.EVALS_DIR / "4_runs/base.jsonl"
    RUN_B = settings.EVALS_DIR / "4_runs/qlora.jsonl"

    OUTPUT_FILE = settings.EVALS_DIR / "5_judge" / "judge_eval.jsonl"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_a = load_jsonl(RUN_A)
    run_b = load_jsonl(RUN_B)

    if not settings.GEMINI_API_KEY:
        raise ValueError("API Key is missing from your environment setup or .env file!")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
                start_time_base = time.perf_counter()
                base_eval = await evaluate_single_response(
                    client,
                    a,
                    a["response"],
                )
                judge_latency_base = time.perf_counter() - start_time_base

                # --- Evaluate QLoRA Model ---
                start_time_qlora = time.perf_counter()
                qlora_eval = await evaluate_single_response(
                    client,
                    a,
                    b["response"],
                )
                judge_latency_qlora = time.perf_counter() - start_time_qlora

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
            await asyncio.sleep(30)

    print(f"\n[+] Evaluation complete.\n[+] Output file: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
