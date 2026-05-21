import asyncio
import json
from datetime import datetime
import pandas as pd # Still used exclusively for safe date normalization

from app.core.settings import settings
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from evals.batch_orchestrator import BatchOrchestrator

INPUT_FILE = settings.EVALS_DIR / "2_processed/jsonl/test_dataset.jsonl"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_FILE = (
    settings.EVALS_DIR 
    / "3_enriched" 
    / f"context_prepared_{timestamp}.jsonl"
)

def normalize_date(value):
    if not value or pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return None

async def main():
    # Only initialize contextual tools
    rag_engine = RAGEngine()
    mcp_manager = MCPManager()
    
    print(f"Reading from: {INPUT_FILE}")
    print(f"Writing context to: {OUTPUT_FILE}")

    # Instantiate orchestrator stub for data structures
    orchestrator = BatchOrchestrator(llm=None, rag=rag_engine, mcp=mcp_manager, resolver=None)

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            if not line.strip():
                continue
                
            item = json.loads(line)
            intent = item.get("intent", "LLM").upper().strip()
            query = item.get("question", "")
            params = item.get("params", {})

            print(f"Extracting context for ID: {item.get('id')} [{intent}]")

            context = None
            tool_result = None
            status = "SUCCESS"

            try:
                if intent == "RAG":
                    context = rag_engine.retrieve_context(query)
                    if not context.strip():
                        status = "NOT_FOUND"

                elif intent in ["FLIGHT", "HOTEL", "WEATHER"]:
                    # Adapt internal structure mapping for legacy Orchestrator compatibility
                    row_adapter = {
                        "departure_id": params.get("departure_id"),
                        "arrival_id": params.get("arrival_id"),
                        "location": params.get("location"),
                        "start_date": normalize_date(params.get("start_date")),
                        "end_date": normalize_date(params.get("end_date"))
                    }
                    
                    mcp_params = orchestrator._build_mcp_params(intent, query, row_adapter)
                    raw_result = await mcp_manager.execute(intent, mcp_params)
                    status = raw_result.get("status", "SUCCESS")
                    tool_result = orchestrator._build_mcp_context(intent, raw_result)

            except Exception as e:
                status = "ERROR"
                tool_result = f"Failed to gather context: {str(e)}"

            # Save full context snapshot metadata 
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

    print("Stage 1 context building successfully complete.")

if __name__ == "__main__":
    asyncio.run(main())
