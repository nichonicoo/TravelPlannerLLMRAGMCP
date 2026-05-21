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


# To generate results
1. Make the dataset, you can make it in either json or excel, you can see the example in evals/1_inputs/{excel/json}
2. use uv run {excel/json}_to_data.py to convert the dataset to jsonl
    (you can rename the output file on the respective file)
3. copy the output jsonl file name and put it as INPUT_FILE on run_context_fetch.py
4. uv run python -m evals.run_context_fetch
5. copy the output jsonl file name and put it as INPUT_FILE on run_inference.py
6. uv run python -m evals.run_inference

# Don't forget to use env for adapter or non adapter usage
