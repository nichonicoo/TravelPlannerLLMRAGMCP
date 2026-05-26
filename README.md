# INTELLIGENT TRAVEL PLANNER ASSISTANT IMPLEMENTING RAG MCP LLM

## 📦 Installation

```bash
pip install -r requirements.txt
```
1. Create venv-be -> pip install -r requirements.txt
2. Create venv-webui pip install -r webui-requirements.txt

Run in paralel. 


# To use the app/main.py
1. install uv
2. uv sync
3. uv run uvicorn app.main:app --reload
4. go to ke 127.0.0.1/8000/docs atau localhost:8000/docs

# To use the app/run_batch.py
1. install uv
2. uv sync
3. uv run python -m app.run_batch


# To prepare the data (rag, mcp)
1. Make the dataset, you can make it in either json or excel, you can see the example in evals/1_inputs/{excel/json}
2. use uv run {excel/json}_to_data.py to convert the dataset to jsonl
    (you can rename the output file on the respective file)
3. copy the output jsonl file name and put it as INPUT_FILE on run_context_fetch.py
4. uv run python -m evals.run_context_fetch

# To generate the results
1. The code will take the latest file of the format of context_prepared_*.jsonl in evals/3_enriched
2. uv run python -m evals.run_inference

# To run scoring
1. Rename the results from run_inference of base to base.jsonl and qlora to qlora.jsonl
2. uv run python -m evals.run_scoring

# To make it readable
1. Rename the results from run_scoring to judge_eval.jsonl
2. uv run python -m evals.convert_jsonl_to_readable
3. The code will generate files in evals/6_readable

# Don't forget to use env for adapter or non adapter usage
