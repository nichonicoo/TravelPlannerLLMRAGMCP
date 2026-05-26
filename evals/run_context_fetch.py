import asyncio
import json
from datetime import datetime

from app.core.settings import settings
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from evals.utils_context import build_mcp_params, build_mcp_context

INPUT_FILE = settings.EVALS_DIR / "2_processed/jsonl/test_dataset.jsonl"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = settings.EVALS_DIR / "3_enriched" / f"context_prepared_{timestamp}.jsonl"

async def main():
    rag_engine = RAGEngine()
    mcp_manager = MCPManager()
    
    print(f"Reading targets from: {INPUT_FILE}")
    print(f"Writing enriched output to: {OUTPUT_FILE}")

    # Safety constraint: create the directory paths if they don't exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            if not line.strip():
                continue
                
            item = json.loads(line)
            intent = item.get("intent", "LLM").upper().strip()
            query = item.get("question", "")
            params = item.get("params", {})

            print(f"Gathering context for Dataset ID: {item.get('id')} [{intent}]")

            context = None
            tool_result = None
            status = "SUCCESS"

            try:
                if intent == "RAG":
                    context = rag_engine.retrieve_context(query)
                    if not context or not context.strip():
                        status = "NOT_FOUND"

                elif intent in ["FLIGHT", "HOTEL", "WEATHER"]:
                    mcp_params = build_mcp_params(intent, query, params)
                    raw_result = await mcp_manager.execute(intent, mcp_params)
                    status = raw_result.get("status", "SUCCESS")
                    tool_result = build_mcp_context(intent, raw_result)

            except Exception as e:
                status = "ERROR"
                tool_result = f"Failed to gather context: {str(e)}"

            out_payload = {
                "id": item.get("id"),
                "intent": intent,
                "question": query,
                "params": params,
                "status": status,
                "context": context,
                "tool_result": tool_result
            }
            outfile.write(json.dumps(out_payload, ensure_ascii=False) + "\n")

    print("\n[+] Stage 1: Context building successfully complete.")

if __name__ == "__main__":
    asyncio.run(main())
