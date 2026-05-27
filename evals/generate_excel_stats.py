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
            item = json.loads(line)
            if "id" in item:
                data[item["id"]] = item
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
    
    # 2. Menggabungkan data secara horizontal per ID
    for record_id, judge in judge_data.items():
        if "judge_error" in judge:
            continue
            
        b_raw = base_raw.get(record_id, {})
        q_raw = qlora_raw.get(record_id, {})
        b_anl = base_analysis.get(record_id, {})
        q_anl = qlora_analysis.get(record_id, {})
        
        rows.append({
            "ID": record_id,
            "Intent": judge.get("intent"),
            "Winner_Model": judge.get("winner_model"),
            "Score_Delta": judge.get("score_delta"),
            
            # ================= BASE MODEL METRICS =================
            "Base_Score_Weighted": judge.get("base_score_raw"),
            "Base_Score_Percent": judge.get("base_score_percent"),
            "Base_Correctness": judge.get("base_metrics", {}).get("correctness"),
            "Base_Groundedness": judge.get("base_metrics", {}).get("groundedness"),
            "Base_Completeness": judge.get("base_metrics", {}).get("completeness"),
            "Base_Clarity": judge.get("base_metrics", {}).get("clarity"),
            "Base_Helpfulness": judge.get("base_metrics", {}).get("helpfulness"),
            "Base_Hallucination_Severity": judge.get("base_hallucination", {}).get("severity", 0),
            
            # Performa dari base.jsonl
            "Base_Latency_Sec": b_raw.get("latency"),
            "Base_TTFT_Sec": b_raw.get("ttft_sec"),
            "Base_Throughput_TokSec": b_raw.get("throughput_tok_sec"),
            
            # Analisis dari base_analysis.json
            "Base_Token_Confidence": b_anl.get("avg_token_confidence"),
            "Base_Token_Entropy": b_anl.get("avg_token_entropy"),
            
            # ================= QLoRA MODEL METRICS =================
            "QLoRA_Score_Weighted": judge.get("qlora_score_raw"),
            "QLoRA_Score_Percent": judge.get("qlora_score_percent"),
            "QLoRA_Correctness": judge.get("qlora_metrics", {}).get("correctness"),
            "QLoRA_Groundedness": judge.get("qlora_metrics", {}).get("groundedness"),
            "QLoRA_Completeness": judge.get("qlora_metrics", {}).get("completeness"),
            "QLoRA_Clarity": judge.get("qlora_metrics", {}).get("clarity"),
            "QLoRA_Helpfulness": judge.get("qlora_metrics", {}).get("helpfulness"),
            "QLoRA_Hallucination_Severity": judge.get("qlora_hallucination", {}).get("severity", 0),
            
            # Performa dari qlora.jsonl
            "QLoRA_Latency_Sec": q_raw.get("latency"),
            "QLoRA_TTFT_Sec": q_raw.get("ttft_sec"),
            "QLoRA_Throughput_TokSec": q_raw.get("throughput_tok_sec"),
            
            # Analisis dari qlora_analysis.json
            "QLoRA_Token_Confidence": q_anl.get("avg_token_confidence"),
            "QLoRA_Token_Entropy": q_anl.get("avg_token_entropy"),
        })

    if not rows:
        print("[-] Tidak ada data yang berhasil digabungkan. Periksa kembali kecocokan ID.")
        return

    df_detail = pd.DataFrame(rows)
    
    # 3. Menghitung Nilai Rata-rata (Summary) untuk Kebutuhan Tabel Bab 4 / Paper
    summary_metrics = [
        ("Weighted Score (1-5)", "Base_Score_Weighted", "QLoRA_Score_Weighted"),
        ("Score Percentage (%)", "Base_Score_Percent", "QLoRA_Score_Percent"),
        ("Correctness (1-5)", "Base_Correctness", "QLoRA_Correctness"),
        ("Groundedness (1-5)", "Base_Groundedness", "QLoRA_Groundedness"),
        ("Completeness (1-5)", "Base_Completeness", "QLoRA_Completeness"),
        ("Clarity (1-5)", "Base_Clarity", "QLoRA_Clarity"),
        ("Helpfulness (1-5)", "Base_Helpfulness", "QLoRA_Helpfulness"),
        ("Hallucination Severity (0-3)", "Base_Hallucination_Severity", "QLoRA_Hallucination_Severity"),
        ("Inference Latency (sec)", "Base_Latency_Sec", "QLoRA_Latency_Sec"),
        ("Time to First Token / TTFT (sec)", "Base_TTFT_Sec", "QLoRA_TTFT_Sec"),
        ("Throughput (tokens/sec)", "Base_Throughput_TokSec", "QLoRA_Throughput_TokSec"),
        ("Avg Token Confidence", "Base_Token_Confidence", "QLoRA_Token_Confidence"),
        ("Avg Token Entropy", "Base_Token_Entropy", "QLoRA_Token_Entropy")
    ]
    
    summary_rows = []
    for metric_label, base_col, qlora_col in summary_metrics:
        summary_rows.append({
            "Metrik Evaluasi": metric_label,
            "Base Model (Mean)": round(df_detail[base_col].mean(), 4) if base_col in df_detail.columns else None,
            "QLoRA Model (Mean)": round(df_detail[qlora_col].mean(), 4) if qlora_col in df_detail.columns else None
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

# Contoh eksekusi alur pemrosesan data:
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
