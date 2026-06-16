import json
import pandas as pd
from pathlib import Path

def load_jsonl_to_dict(path: Path) -> dict:
    """Utility untuk memuat file JSONL ke dalam dictionary berdasarkan 'id'."""
    data = {}
    if not path.exists():
        print(f"[!] Peringatan: Berkas {path} tidak ditemukan.")
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
    # 1. Memuat seluruh sumber data eksternal
    judge_data = load_jsonl_to_dict(judge_jsonl_path)
    base_raw = load_jsonl_to_dict(base_jsonl_path)
    qlora_raw = load_jsonl_to_dict(qlora_jsonl_path)
    base_analysis = load_jsonl_to_dict(base_analysis_jsonl_path)
    qlora_analysis = load_jsonl_to_dict(qlora_analysis_jsonl_path)

    rows = []
    
    # 2. Menggabungkan data secara horizontal menggunakan jangkar master ID
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
        
        # --- PERBAIKAN: Jalur ekstraksi datar sesuai struktur judge_eval.json ---
        base_metrics = judge.get("base_metrics", {})
        qlora_metrics = judge.get("qlora_metrics", {})
        
        base_score_pct = judge.get("base_score_percent")
        qlora_score_pct = judge.get("qlora_score_percent")
        
        # Ambil tingkat keparahan halusinasi secara aman dari root object
        base_hal_sev = judge.get("base_hallucination", {}).get("severity", 0) if judge.get("base_hallucination") else 0
        qlora_hal_sev = judge.get("qlora_hallucination", {}).get("severity", 0) if judge.get("qlora_hallucination") else 0
        
        # Mengambil nilai dimensi individual (1-5)
        b_corr = base_metrics.get("correctness")
        b_grou = base_metrics.get("groundedness")
        b_comp = base_metrics.get("completeness")
        b_clar = base_metrics.get("clarity")
        b_help = base_metrics.get("helpfulness")
        
        q_corr = qlora_metrics.get("correctness")
        q_grou = qlora_metrics.get("groundedness")
        q_comp = qlora_metrics.get("completeness")
        q_clar = qlora_metrics.get("clarity")
        q_help = qlora_metrics.get("helpfulness")
        
        # Hitung rata-rata Nilai Weighted Score secara manual (Mengabaikan nilai None)
        b_weights = [v for v in [b_corr, b_grou, b_comp, b_clar, b_help] if v is not None]
        base_score_weighted = sum(b_weights) / len(b_weights) if b_weights else None
        
        q_weights = [v for v in [q_corr, q_grou, q_comp, q_clar, q_help] if v is not None]
        qlora_score_weighted = sum(q_weights) / len(q_weights) if q_weights else None
        
        # Ekstraksi jumlah token alternatif
        base_tokens = b_raw.get("response_tokens_count") or b_anl.get("response_tokens_count", 0)
        qlora_tokens = q_raw.get("response_tokens_count") or q_anl.get("response_tokens_count", 0)

        rows.append({
            "ID": record_id,
            "Intent": intent,
            "Winner_Model": judge.get("winner_model", "TIE"),
            "Score_Delta": judge.get("score_delta", 0),
            
            # ================= BASE MODEL METRICS =================
            "Base_Score_Weighted": base_score_weighted,
            "Base_Score_Percent": base_score_pct,
            "Base_Correctness": b_corr,
            "Base_Groundedness": b_grou,
            "Base_Completeness": b_comp,
            "Base_Clarity": b_clar,
            "Base_Helpfulness": b_help,
            "Base_Hallucination_Severity": base_hal_sev,
            "Base_Has_Hallucination": 1 if base_hal_sev > 0 else 0,
            
            # Performa dengan Coalesce + fallback dari log judge jika file run kosong
            "Base_Latency_Sec": b_raw.get("latency") or b_anl.get("latency") or judge.get("judge_latency_sec_base"),
            "Base_TTFT_Sec": b_raw.get("ttft_sec") or b_anl.get("ttft_sec"),
            "Base_Throughput_TokSec": b_raw.get("throughput_tok_sec") or b_anl.get("throughput_tok_sec"),
            "Base_Token_Count": base_tokens,
            "Base_Token_Confidence": b_anl.get("avg_token_confidence"),
            "Base_Token_Entropy": b_anl.get("avg_token_entropy"),
            
            # ================= QLoRA MODEL METRICS =================
            "QLoRA_Score_Weighted": qlora_score_weighted,
            "QLoRA_Score_Percent": qlora_score_pct,
            "QLoRA_Correctness": q_corr,
            "QLoRA_Groundedness": q_grou,
            "QLoRA_Completeness": q_comp,
            "QLoRA_Clarity": q_clar,
            "QLoRA_Helpfulness": q_help,
            "QLoRA_Hallucination_Severity": qlora_hal_sev,
            "QLoRA_Has_Hallucination": 1 if qlora_hal_sev > 0 else 0,
            
            # Performa dengan Coalesce + fallback dari log judge jika file run kosong
            "QLoRA_Latency_Sec": q_raw.get("latency") or q_anl.get("latency") or judge.get("judge_latency_sec_qlora"),
            "QLoRA_TTFT_Sec": q_raw.get("ttft_sec") or q_anl.get("ttft_sec"),
            "QLoRA_Throughput_TokSec": q_raw.get("throughput_tok_sec") or q_anl.get("throughput_tok_sec"),
            "QLoRA_Token_Count": qlora_tokens,
            "QLoRA_Token_Confidence": q_anl.get("avg_token_confidence"),
            "QLoRA_Token_Entropy": q_anl.get("avg_token_entropy"),
        })

    if not rows:
        print("[-] Tidak ada data yang berhasil digabungkan. Periksa kembali kecocokan ID.")
        return

    df_detail = pd.DataFrame(rows)
    
    # 3. Menghitung Nilai Rata-rata (Summary) menggunakan nama kolom yang sinkron
    summary_metrics = [
        ("Weighted Score (1-5)", "Base_Score_Weighted", "QLoRA_Score_Weighted"),
        ("Score Percentage (%)", "Base_Score_Percent", "QLoRA_Score_Percent"),
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
    
    summary_rows = []
    for metric_label, base_col, qlora_col in summary_metrics:
        summary_rows.append({
            "Metrik Evaluasi": metric_label,
            "Base Model (Mean)": round(df_detail[base_col].mean(), 4) if base_col in df_detail.columns and pd.notna(df_detail[base_col].mean()) else None,
            "QLoRA Model (Mean)": round(df_detail[qlora_col].mean(), 4) if qlora_col in df_detail.columns and pd.notna(df_detail[qlora_col].mean()) else None
        })
        
    df_summary = pd.DataFrame(summary_rows)

    # 4. Ekspor ke berkas Excel dengan konfigurasi dua Sheet
    output_excel_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Ringkasan_Paper", index=False)
        df_detail.to_excel(writer, sheet_name="Detail_Per_Pertanyaan", index=False)
        
    print(f"[+] Kompilasi data sukses.")
    print(f"    -> Sheet 'Ringkasan_Paper' berisi rata-rata komparatif.")
    print(f"    -> Sheet 'Detail_Per_Pertanyaan' berisi baris data lengkap.")
    print(f"    -> Lokasi berkas: {output_excel_path}")

if __name__ == "__main__":
    EVALS_DIR = Path("./evals")
    
    aggregate_eval_to_excel(
        judge_jsonl_path=EVALS_DIR / "5_judge/judge_eval.jsonl",
        base_jsonl_path=EVALS_DIR / "4_runs/base.jsonl",
        qlora_jsonl_path=EVALS_DIR / "4_runs/qlora.jsonl",
        base_analysis_jsonl_path=EVALS_DIR / "4_runs/base_analysis.jsonl",
        qlora_analysis_jsonl_path=EVALS_DIR / "4_runs/qlora_analysis.jsonl",
        output_excel_path=EVALS_DIR / "6_results/rekap_evaluasi_skripsi.xlsx"
    )
