import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from app.core.settings import settings
from app.infrastructure.llm.llm_factory import create_llm_provider
from evals.prompts import LLM_PROMPT, RAG_PROMPT, MCP_PROMPT

# Specify your generated intermediate stage 1 file path here
STAGE1_INPUT_FILE = settings.EVALS_DIR / "3_enriched/context_prepared_CHANGEME.jsonl"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
provider = settings.LLM_PROVIDER
model_name = settings.HF_MODEL_NAME.split("/")[-1].replace("-", "_")
adapter_name = settings.HF_ADAPTER_NAME.split("/")[-1].replace("-", "_") if settings.HF_ADAPTER_NAME else "base"

OUTPUT_FILE = (
    settings.EVALS_DIR 
    / "4_final" 
    / f"final_inference_{provider}_{model_name}_{adapter_name}_{timestamp}.jsonl"
)

def build_messages(system_prompt: str, query: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

async def main():
    # Initialize ONLY LLM resources for rapid inferencing
    llm = create_llm_provider()
    
    print(f"Running inference from context cache: {STAGE1_INPUT_FILE}")
    print(f"Writing definitive responses to: {OUTPUT_FILE}")

    with open(STAGE1_INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            if not line.strip():
                continue
                
            data = json.loads(line)
            intent = data["intent"]
            query = data["question"]
            status = data["status"]
            context = data["context"]
            tool_result = data["tool_result"]

            # Retain error tracking state from earlier stage blocks
            if status == "ERROR":
                data["response"] = "Skipped generation due to previous Phase 1 contextual errors."
                data["latency"] = 0.0
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                continue

            start_time = time.perf_counter()
            response = ""

            try:
                if intent == "LLM":
                    messages = build_messages(LLM_PROMPT, query)
                    response = await llm.generate(messages)
                    
                elif intent == "RAG":
                    if status == "NOT_FOUND":
                        response = "Informasi tidak ditemukan."
                    else:
                        system_prompt = RAG_PROMPT.format(context=context)
                        messages = build_messages(system_prompt, query)
                        response = await llm.generate(messages)
                        
                elif intent in ["FLIGHT", "HOTEL", "WEATHER"]:
                    system_prompt = MCP_PROMPT.format(tool_result=tool_result)
                    messages = build_messages(system_prompt, query)
                    response = await llm.generate(messages)
                
                data["inference_status"] = "SUCCESS"
            except Exception as e:
                data["inference_status"] = "GENERATION_ERROR"
                response = f"Runtime generation fault detected: {str(e)}"

            latency = time.perf_counter() - start_time
            
            # Enrich object structural integrity
            data["response"] = response
            data["latency"] = round(latency, 3)
            
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"Inference job complete. File updated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
