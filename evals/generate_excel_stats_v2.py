import json
import pandas as pd
from pathlib import Path

def load_jsonl_to_dict(path: Path) -> dict:
    """Safely loads JSONL files into a dictionary mapped by 'id'."""
    data = {}
    if not path.exists():
        print(f"[!] Warning: File {path.name} not found.")
        return data
        
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if "id" in item:
                    data[item["id"]] = item
            except json.JSONDecodeError:
                continue
    return data

def aggregate_eval_to_excel(
    judge_jsonl_path: Path, 
    base_jsonl_path: Path, 
    qlora_jsonl_path: Path,
    base_analysis_jsonl_path: Path,
    qlora_analysis_jsonl_path: Path,
    output_excel_path: Path
):
    # 1. Load all datasets
    judge_data = load_jsonl_to_dict(judge_jsonl_path)
    base_raw = load_jsonl_to_dict(base_jsonl_path)
    qlora_raw = load_jsonl_to_dict(qlora_jsonl_path)
    base_analysis = load_jsonl_to_dict(base_analysis_jsonl_path)
    qlora_analysis = load_jsonl_to_dict(qlora_analysis_jsonl_path)

    rows = []
    
    # 2. Master ID collection
    master_ids = set(judge_data.keys()).union(base_raw.keys()).union(base_analysis.keys())
    
    for record_id in sorted(master_ids):
        judge = judge_data.get(record_id, {})
        b_raw = base_raw.get(record_id, {})
        q_raw = qlora_raw.get(record_id, {})
        b_anl = base_analysis.get(record_id, {})
        q_anl = qlora_analysis.get(record_id, {})
        
        if "judge_error" in judge and len(judge) == 1:
            continue 
            
        intent_raw = judge.get("intent") or b_raw.get("intent") or b_anl.get("intent") or "UNKNOWN"
        intent = intent_raw.upper()
        
        # --- Metrics 1-5 Extraction ---
        base_metrics = judge.get("base_metrics", {})
        qlora_metrics = judge.get("qlora_metrics", {})
        
        # --- FIX: Direct map to your real schema variables ---
        b_score_raw = judge.get("base_score_raw")
        q_score_raw = judge.get("qlora_score_raw")
        b_score_pct = judge.get("base_score_percent")
        q_score_pct = judge.get("qlora_score_percent")
        
        # Extract Hallucination objects safely
        base_hal_obj = judge.get("base_hallucination", {}) if isinstance(judge.get("base_hallucination"), dict) else {}
        qlora_hal_obj = judge.get("qlora_hallucination", {}) if isinstance(judge.get("qlora_hallucination"), dict) else {}
        
        base_hal_sev = base_hal_obj.get("severity", 0)
        qlora_hal_sev = qlora_hal_obj.get("severity", 0)
        
        # Token sizes 
        base_tokens = b_raw.get("response_tokens_count") or b_anl.get("response_tokens_count") or judge.get("judge_token_count_base", 0)
        qlora_tokens = q_raw.get("response_tokens_count") or q_anl.get("response_tokens_count") or judge.get("judge_token_count_qlora", 0)

        rows.append({
            "ID": record_id,
            "Intent": intent,
            "Winner_Model": judge.get("winner_model", "TIE"),
            
            # --- GLOBAL OVERALL RAW & PCT SCORES ---
            "Base_Overall_Raw": b_score_raw,
            "QLoRA_Overall_Raw": q_score_raw,
            "Base_Overall_Pct": b_score_pct,
            "QLoRA_Overall_Pct": q_score_pct,
            "Score_Delta": judge.get("score_delta"),
            
            # --- BASE MODEL METRICS ---
            "Base_Correctness": base_metrics.get("correctness"),
            "Base_Groundedness": base_metrics.get("groundedness"),
            "Base_Completeness": base_metrics.get("completeness"),
            "Base_Clarity": base_metrics.get("clarity"),
            "Base_Helpfulness": base_metrics.get("helpfulness"),
            "Base_Hallucination_Severity": base_hal_sev,
            "Base_Has_Hallucination": 1 if base_hal_sev > 0 else 0,
            "Base_Latency_Sec": b_raw.get("latency") or b_anl.get("latency") or judge.get("judge_latency_sec_base"),
            "Base_TTFT_Sec": b_raw.get("ttft_sec") or b_anl.get("ttft_sec"),
            "Base_Throughput_TokSec": b_raw.get("throughput_tok_sec") or b_anl.get("throughput_tok_sec"),
            "Base_Token_Count": base_tokens,
            "Base_Token_Confidence": b_anl.get("avg_token_confidence"),
            "Base_Token_Entropy": b_anl.get("avg_token_entropy"),
            
            # --- QLoRA MODEL METRICS ---
            "QLoRA_Correctness": qlora_metrics.get("correctness"),
            "QLoRA_Groundedness": qlora_metrics.get("groundedness"),
            "QLoRA_Completeness": qlora_metrics.get("completeness"),
            "QLoRA_Clarity": qlora_metrics.get("clarity"),
            "QLoRA_Helpfulness": qlora_metrics.get("helpfulness"),
            "QLoRA_Hallucination_Severity": qlora_hal_sev,
            "QLoRA_Has_Hallucination": 1 if qlora_hal_sev > 0 else 0,
            "QLoRA_Latency_Sec": q_raw.get("latency") or q_anl.get("latency") or judge.get("judge_latency_sec_qlora"),
            "QLoRA_TTFT_Sec": q_raw.get("ttft_sec") or q_anl.get("ttft_sec"),
            "QLoRA_Throughput_TokSec": q_raw.get("throughput_tok_sec") or q_anl.get("throughput_tok_sec"),
            "QLoRA_Token_Count": qlora_tokens,
            "QLoRA_Token_Confidence": q_anl.get("avg_token_confidence"),
            "QLoRA_Token_Entropy": q_anl.get("avg_token_entropy"),
        })

    if not rows:
        print("[-] Error: No matching items found across files.")
        return

    df_detail = pd.DataFrame(rows)
    
    # 3. Comprehensive Metric Definitions for the Averages
    summary_metrics = [
        ("Overall Score (Raw Average)", "Base_Overall_Raw", "QLoRA_Overall_Raw"),
        ("Overall Score (%)", "Base_Overall_Pct", "QLoRA_Overall_Pct"),
        ("Correctness (1-5)", "Base_Correctness", "QLoRA_Correctness"),
        ("Groundedness (1-5)", "Base_Groundedness", "QLoRA_Groundedness"),
        ("Completeness (1-5)", "Base_Completeness", "QLoRA_Completeness"),
        ("Clarity (1-5)", "Base_Clarity", "QLoRA_Clarity"),
        ("Helpfulness (1-5)", "Base_Helpfulness", "QLoRA_Helpfulness"),
        ("Hallucination Severity (0-3)", "Base_Hallucination_Severity", "QLoRA_Hallucination_Severity"),
        ("Hallucination Rate (Binary %)", "Base_Has_Hallucination", "QLoRA_Has_Hallucination"),
        ("Inference Latency (sec)", "Base_Latency_Sec", "QLoRA_Latency_Sec"),
        ("Time to First Token / TTFT (sec)", "Base_TTFT_Sec", "QLoRA_TTFT_Sec"),
        ("Throughput (tokens/sec)", "Base_Throughput_TokSec", "QLoRA_Throughput_TokSec"),
        ("Generated Tokens Length", "Base_Token_Count", "QLoRA_Token_Count"),
        ("Avg Token Confidence", "Base_Token_Confidence", "QLoRA_Token_Confidence"),
        ("Avg Token Entropy", "Base_Token_Entropy", "QLoRA_Token_Entropy")
    ]
    
    # A. Global Macro Summary
    summary_rows = []
    for metric_label, base_col, qlora_col in summary_metrics:
        b_mean = df_detail[base_col].mean() if base_col in df_detail.columns else None
        q_mean = df_detail[qlora_col].mean() if qlora_col in df_detail.columns else None
        
        summary_rows.append({
            "Metrik Evaluasi": metric_label,
            "Base Model (Mean)": round(b_mean, 4) if pd.notna(b_mean) else None,
            "QLoRA Model (Mean)": round(q_mean, 4) if pd.notna(q_mean) else None
        })
    df_summary = pd.DataFrame(summary_rows)

    # B. Intent Summary Breakdown
    intent_rows = []
    unique_intents = sorted(df_detail["Intent"].unique())
    for intent_name in unique_intents:
        df_intent = df_detail[df_detail["Intent"] == intent_name]
        for metric_label, base_col, qlora_col in summary_metrics:
            b_int_mean = df_intent[base_col].mean() if base_col in df_intent.columns else None
            q_int_mean = df_intent[qlora_col].mean() if qlora_col in df_intent.columns else None
            
            intent_rows.append({
                "Intent": intent_name,
                "Metrik Evaluasi": metric_label,
                "Base Model (Mean)": round(b_int_mean, 4) if pd.notna(b_int_mean) else None,
                "QLoRA Model (Mean)": round(q_int_mean, 4) if pd.notna(q_int_mean) else None
            })
    df_intent_summary = pd.DataFrame(intent_rows)

    # C. Win-Rate Distribution Breakdown
    win_counts = df_detail["Winner_Model"].value_counts(normalize=True) * 100
    df_win_rate = pd.DataFrame({
        "Model Verdict": win_counts.index,
        "Percentage Share (%)": win_counts.round(2).values
    })

    # 4. Write to Excel sheets
    output_excel_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Ringkasan_Global", index=False)
        df_intent_summary.to_excel(writer, sheet_name="Ringkasan_Per_Intent", index=False)
        df_win_rate.to_excel(writer, sheet_name="Win_Rate_Distribution", index=False)
        df_detail.to_excel(writer, sheet_name="Detail_Per_Pertanyaan", index=False)
        
    print(f"[+] Complete aggregation successful! 4 sheets created at: {output_excel_path}")

if __name__ == "__main__":
    EVALS_DIR = Path("./evals")
    aggregate_eval_to_excel(
        judge_jsonl_path=EVALS_DIR / "5_judge/judge_eval.jsonl",
        base_jsonl_path=EVALS_DIR / "4_runs/base.jsonl",
        qlora_jsonl_path=EVALS_DIR / "4_runs/qlora.jsonl",
        base_analysis_jsonl_path=EVALS_DIR / "4_runs/base_analysis.jsonl",
        qlora_analysis_jsonl_path=EVALS_DIR / "4_runs/qlora_analysis.jsonl",
        output_excel_path=EVALS_DIR / "6_results/rekap_evaluasi_skripsi_v2.xlsx"
    )
