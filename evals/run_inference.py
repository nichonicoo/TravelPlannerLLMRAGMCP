import asyncio
import json
import time
import sys
from datetime import datetime
from pathlib import Path

from app.core.settings import settings
from app.infrastructure.llm.llm_factory import create_llm_provider
from evals.prompts import (
    LLM_PROMPT,
    RAG_PROMPT,
    MCP_PROMPT,
    MCP_FLIGHT_PROMPT,
    MCP_HOTEL_PROMPT,
    MCP_WEATHER_PROMPT
)


def get_latest_context_file(directory: Path) -> Path:
    """Automatically grabs the newest enriched context snapshot file."""
    files = list(directory.glob("context_prepared_*.jsonl"))
    if not files:
        raise FileNotFoundError(
            f"No enriched context snapshots found in {directory}")
    return max(files, key=lambda p: p.stat().st_mtime)


def build_messages(system_prompt: str, query: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]


async def main():
    context_dir = settings.EVALS_DIR / "3_enriched"

    try:
        # INPUT_FILE = settings.EVALS_DIR / \
        #     "3_enriched/context_prepared_20260521_230508.jsonl"
        INPUT_FILE = get_latest_context_file(context_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Setup definitive generation timestamp and file tracking paths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    provider = settings.LLM_PROVIDER
    model_name = settings.HF_MODEL_NAME.split("/")[-1].replace("-", "_")
    adapter_name = settings.HF_ADAPTER_NAME.split(
        "/")[-1].replace("-", "_") if settings.HF_ADAPTER_NAME else "base"

    OUTPUT_FILE = (
        settings.EVALS_DIR
        / "4_runs"
        / f"final_inference_{provider}_{model_name}_{adapter_name}_{timestamp}.jsonl"
    )

    # Ensure output directory runs path exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Initialize strictly the target LLM resources
    llm = create_llm_provider()

    print(f"[*] Target Model:   {model_name}")
    print(f"[*] Active Adapter:  {adapter_name}")
    print(f"[*] Reading Cache:   {INPUT_FILE.name}")
    print(f"[*] Target Output:   {OUTPUT_FILE.name}\n" + "-" * 60)

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
            open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            if not line.strip():
                continue

            data = json.loads(line)
            intent = data["intent"].upper().strip()
            query = data["question"]
            status = data["status"]
            context = data["context"]
            tool_result = data["tool_result"]

            # Guard Clause: Retain context collection pipeline errors
            if status == "ERROR" and (tool_result is None or tool_result == "" or context is None or context == ""):
                data["response"] = None
                data["inference_status"] = "SKIPPED_CONTEXT_ERROR"
                data["latency"] = 0.0
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                continue

            # Handled expected empty search state gracefully without wasting tokens
            if intent == "RAG" and status == "NOT_FOUND":
                data["response"] = "Informasi tidak ditemukan."
                data["inference_status"] = "SUCCESS_EMPTY_RAG"
                data["latency"] = 0.0
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                continue

            # Select prompt structure cleanly based on current key mapping
            try:
                if intent == "LLM":
                    system_prompt = LLM_PROMPT
                elif intent == "RAG":
                    system_prompt = RAG_PROMPT.format(context=context)
                elif intent in ["FLIGHT", "HOTEL", "WEATHER"]:
                    # default fallback
                    system_prompt = MCP_PROMPT.format(
                        tool_result=tool_result
                    )

                    parsed_tool = []
                    if tool_result:
                        try:
                            parsed_tool = json.loads(tool_result)
                        except Exception:
                            parsed_tool = []

                    total_opsi = len(parsed_tool) if isinstance(
                        parsed_tool, list) else 1

                    if intent == "FLIGHT":
                        system_prompt = MCP_FLIGHT_PROMPT.format(
                            tool_result=tool_result,
                            total_opsi=total_opsi
                        )
                    elif intent == "HOTEL":
                        system_prompt = MCP_HOTEL_PROMPT.format(
                            tool_result=tool_result,
                            total_opsi=total_opsi
                        )
                    elif intent == "WEATHER":
                        system_prompt = MCP_WEATHER_PROMPT.format(
                            tool_result=tool_result
                        )
                else:
                    raise ValueError(
                        f"Unsupported pipeline intent track: {intent}")

                messages = build_messages(system_prompt, query)

                # Execution Timing Block
                start_time = time.perf_counter()
                
                # Capture the complete metrics payload dict from provider
                gen_payload = await llm.generate(messages, mode=settings.LLM_GENERATION_MODE)
                
                total_latency = time.perf_counter() - start_time

                # Map metrics directly to output fields
                data["response"] = gen_payload["response"]
                data["latency"] = round(total_latency, 3)
                data["ttft_sec"] = gen_payload["ttft_sec"]
                data["throughput_tok_sec"] = gen_payload["throughput_tok_sec"]
                data["avg_token_confidence"] = gen_payload["avg_token_confidence"]
                data["avg_token_entropy"] = gen_payload["avg_token_entropy"]
                data["inference_status"] = "SUCCESS"

            except Exception as runtime_error:
                data["response"] = None
                data["latency"] = round(time.perf_counter() - start_time, 3) if 'start_time' in locals() else 0.0
                data["ttft_sec"] = None
                data["throughput_tok_sec"] = None
                data["avg_token_confidence"] = None
                data["avg_token_entropy"] = None
                data["inference_status"] = "GENERATION_ERROR"
                data["error_log"] = str(runtime_error)

            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"\n[+] Stage 2: Inference execution batch job complete.")

if __name__ == "__main__":
    asyncio.run(main())
