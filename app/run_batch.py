import asyncio
import pandas as pd
from datetime import datetime

from app.core.settings import settings
from app.infrastructure.llm.llm_factory import create_llm_provider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.services.eval.batch_chat_service import BatchChatService
from app.services.resolver import Resolver


INPUT_FILE = settings.EVALS_DIR / "datasets/test_dataset.xlsx"
timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

provider = settings.LLM_PROVIDER

model_name = (
    settings.HF_MODEL_NAME
    .split("/")[-1]
    .replace("-", "_")
)

adapter_name = settings.HF_ADAPTER_NAME

if adapter_name:
    adapter_name = (
        adapter_name
        .split("/")[-1]
        .replace("-", "_")
    )
else:
    adapter_name = "base"

output_name = (
    f"{provider}_"
    f"{model_name}_"
    f"{adapter_name}_"
    f"{timestamp}.xlsx"
)

OUTPUT_FILE = (
    settings.EVALS_DIR
    / "outputs"
    / output_name
)

print(INPUT_FILE)
print(OUTPUT_FILE)


async def main():
    # Setup dependencies
    llm = create_llm_provider()
    rag_engine = RAGEngine()
    mcp_manager = MCPManager()
    resolver = Resolver()

    service = BatchChatService(
        llm=llm,
        rag=rag_engine,
        mcp_manager=mcp_manager,
        resolver=resolver
    )

    # Read excel
    df = pd.read_excel(INPUT_FILE)
    df = df.where(pd.notnull(df), None)

    for col in ["start_date", "end_date"]:
            if col in df.columns:
                # pd.to_datetime ensures everything is unified, then we format it
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
                # Replace any resulting NaN values back to None
                df[col] = df[col].where(pd.notnull(df[col]), None)

    results = []

    for _, row in df.iterrows():

        row_dict = row.to_dict()

        question = row_dict.get("question", "")
        intent = row_dict.get("intent", "LLM")

        print(f"Processing: {row_dict.get('id')}")

        try:
            result = await service.chat(
                intent=intent,
                query=question,
                row=row_dict
            )

        except Exception as e:
            result = {
                "status": "ERROR",
                "response": str(e),
                "latency": None,
            }

        results.append(result)

    # Add output column
    df["response"] = [r.get("response") for r in results]
    df["status"] = [r.get("status") for r in results]
    df["latency"] = [r.get("latency") for r in results]

    # Save result
    df.to_excel(OUTPUT_FILE, index=False)

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
