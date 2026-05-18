import os
import time
import shutil
import pandas as pd

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE_DIR, "documents")
DB_BASE_PATH = os.path.join(BASE_DIR, "benchmark_db")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K = 4

# MODELS
MODELS = {
    "MiniLM": "sentence-transformers/all-MiniLM-L6-v2",
    "E5": "intfloat/e5-base",
    "MultiLingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "BGE-M3": "BAAI/bge-m3"
}

# TEST QUERIES
QUERIES = [
    "ibu kota NTB",
    "gunung tertinggi di NTB",
    "agama mayoritas NTB",
    "sejarah pembentukan NTB",
    "jumlah penduduk NTB",
    "Luas wilayah Sulawesi Utara",
    "Berapa jumlah arca di Rupadhatu",
    "Berapa populasi NTT tahun 2025",
    "Berapa jumlah sampah harian di Labuan Bajo",
    "Berapa jumlah arca pada baris ketiga Rupadhatu",
    "Berapa panjang Candi Borobudur dalam meter",
    "Berapa luas wilayah NTT",
    "Berapa lebar Danau Toba",
    "Berapa tinggi Candi Borobudur",
    "Berapa lebar Candi Borobudur",
    "Berapa penurunan suhu global akibat letusan Toba",
    "Berapa jumlah gunung di Sulawesi Utara",
    "Berapa panjang Danau Toba",
    "Berapa jumlah pulau di Sulawesi Utara",
    "Berapa jumlah arca di Arupadhatu",
    "Berapa kedalaman maksimal Danau Toba",
    "Di sisi mana arca Amitabha berada",
    "Kapan NTB dibentuk",
    "Berapa luas wilayah Labuan Bajo",
    "Berapa populasi NTB tahun 2024",
    "Apa makna mudra Bhumisparsa",
    "Kapan Borobudur dibangun",
    "Berapa luas Danau Toba",
    "Berapa VEI letusan Toba"
]

# LOAD & SPLIT
def load_and_split():
    loader = DirectoryLoader(
        DOC_PATH,
        glob="*.txt",
        loader_cls=lambda path: TextLoader(path, encoding="utf-8")
    )

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    return splitter.split_documents(docs)

# SIMPLE RELEVANCE CHECK
def is_relevant(query, doc_text):
    words = query.lower().split()
    return any(w in doc_text.lower() for w in words)

# BENCHMARK
def benchmark_model(model_name, model_path, base_chunks):
    print(f"\n=== Testing {model_name} ===")

    # copy chunks biar tidak modify global
    chunks = []
    for doc in base_chunks:
        new_doc = doc.copy()
        chunks.append(new_doc)

    # HANDLE E5 FORMAT
    is_e5 = "e5" in model_name.lower()

    if is_e5:
        for doc in chunks:
            doc.page_content = f"passage: {doc.page_content}"

    embeddings = HuggingFaceEmbeddings(model_name=model_path)

    db_path = os.path.join(DB_BASE_PATH, model_name)

    # reset DB biar fair
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    # build DB
    start_time = time.time()
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path
    )
    build_time = time.time() - start_time

    results = []

    for query in QUERIES:
        q = query

        if is_e5:
            q = f"query: {query}"

        q_start = time.time()
        docs = db.similarity_search(q, k=TOP_K)
        latency = time.time() - q_start

        relevant_count = sum(
            is_relevant(query, d.page_content) for d in docs
        )

        results.append({
            "query": query,
            "relevant_docs": relevant_count,
            "latency": latency
        })

    avg_relevance = sum(r["relevant_docs"] for r in results) / len(results)
    avg_latency = sum(r["latency"] for r in results) / len(results)

    return {
        "model": model_name,
        "build_time": build_time,
        "avg_relevance": avg_relevance,
        "avg_latency": avg_latency,
        "details": results
    }

# RUN
def run_benchmark():
    base_chunks = load_and_split()

    print(f"Total chunks: {len(base_chunks)}")

    summary_rows = []
    detail_rows = []

    for name, path in MODELS.items():
        result = benchmark_model(name, path, base_chunks)

        summary_rows.append({
            "model": result["model"],
            "build_time": result["build_time"],
            "avg_relevance": result["avg_relevance"],
            "avg_latency": result["avg_latency"]
        })

        for d in result["details"]:
            detail_rows.append({
                "model": result["model"],
                "query": d["query"],
                "relevant_docs": d["relevant_docs"],
                "latency": d["latency"]
            })

    df_summary = pd.DataFrame(summary_rows)
    df_detail = pd.DataFrame(detail_rows)

    # SCORING (optional)
    df_summary["score"] = (
        df_summary["avg_relevance"] * 0.7 -
        df_summary["avg_latency"] * 0.3
    )

    df_summary = df_summary.sort_values(by="score", ascending=False)

    print("\n=== SUMMARY ===")
    print(df_summary)

    print("\n=== DETAIL ===")
    print(df_detail)

    # SAVE
    df_summary.to_csv("benchmark_summary.csv", index=False)
    df_detail.to_csv("benchmark_detail.csv", index=False)

    return df_summary, df_detail


if __name__ == "__main__":
    run_benchmark()