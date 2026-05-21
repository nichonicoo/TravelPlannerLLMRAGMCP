import asyncio
import pandas as pd

from app.core.settings import settings

INPUT_FILE = settings.EVALS_DIR / "inputs/excels/test_dataset.xlsx"
OUTPUT_FILE = settings.EVALS_DIR / "outputs/output.xlsx"

print(f"Input file path: {INPUT_FILE}")
print(f"Output file path: {OUTPUT_FILE}")

async def main():
    try:
        df = pd.read_excel(INPUT_FILE)
        # This converts NaN/NaT values to Python None for clean checking
        df = df.where(pd.notnull(df), None)
        print(f"Successfully read {len(df)} rows from Excel.\n")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    answers = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        # Core fields
        row_id = row_dict.get("id", f"Row-{idx}")
        question = row_dict.get("question", "")
        intent = row_dict.get("intent", "LLM")

        # Context fields to check for None
        context_fields = [
            "departure_id", 
            "arrival_id", 
            "location", 
            "start_date", 
            "end_date"
        ]

        print(f"--- Processing Row: {row_id} [{intent}] ---")
        print(f"Question: {question}")
        
        # Check and print the status of each extra field
        detected_context = {}
        for field in context_fields:
            val = row_dict.get(field)
            status = "None" if val is None else f"'{val}'"
            print(f"  └─ {field.ljust(13)}: {status}")
            
            if val is not None:
                detected_context[field] = val

        try:
            await asyncio.sleep(0) 
            # Output format to log what was captured in the final Excel
            if detected_context:
                context_str = ", ".join([f"{k}={v}" for k, v in detected_context.items()])
                answer = f"TEST SUCCESS: Captured {context_str}"
            else:
                answer = "TEST SUCCESS: No extra context parameters (Pure Text)"

        except Exception as e:
            answer = f"ERROR: {str(e)}"

        answers.append(answer)
        print("\n")

    # Add output column and save
    df["answer"] = answers
    try:
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"Saved test results successfully to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving output file: {e}")


if __name__ == "__main__":
    asyncio.run(main())
