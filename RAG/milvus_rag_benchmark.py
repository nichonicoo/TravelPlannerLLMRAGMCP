import os
import time
import pandas as pd
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE_DIR, "documents")

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

# QUERIES
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

# SIMPLE RELEVANCE
def is_relevant(query, doc_text):
    words = query.lower().split()
    return any(w in doc_text.lower() for w in words)

# setup collection
def setup_collection(name, dim):
    if utility.has_collection(name):
        utility.drop_collection(name)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
    ]

    schema = CollectionSchema(fields)
    collection = Collection(name=name, schema=schema)

    index_params = {
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {"M": 8, "efConstruction": 64}
    }

    collection.create_index("embedding", index_params)
    return collection

# benchmark
def benchmark_model(model_name, model_path, base_chunks):
    print(f"\n=== Testing {model_name} (Milvus Lite) ===")

    embeddings = HuggingFaceEmbeddings(model_name=model_path)

    dim = len(embeddings.embed_query("test"))

    collection = setup_collection(f"{model_name}_lite", dim)

    texts = [doc.page_content for doc in base_chunks]

    # BUILD
    start_time = time.time()
    vectors = embeddings.embed_documents(texts)

    collection.insert([vectors, texts])
    collection.load()

    build_time = time.time() - start_time

    results = []

    search_params = {
        "metric_type": "COSINE",
        "params": {"ef": 64}
    }

    for query in QUERIES:
        q_vec = embeddings.embed_query(query)

        q_start = time.time()

        res = collection.search(
            data=[q_vec],
            anns_field="embedding",
            param=search_params,
            limit=TOP_K,
            output_fields=["text"]
        )

        latency = time.time() - q_start

        docs = [hit.entity.get("text") for hit in res[0]]

        relevant_count = sum(
            is_relevant(query, d) for d in docs
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

# run
def run_benchmark():
    # milvus lite 
    connections.connect(
        alias="default",
        uri="milvus_lite.db"
    )

    base_chunks = load_and_split()

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

    df_summary["score"] = (
        df_summary["avg_relevance"] * 0.7 -
        df_summary["avg_latency"] * 0.3
    )

    df_summary = df_summary.sort_values(by="score", ascending=False)

    print("\n=== SUMMARY (Milvus Lite) ===")
    print(df_summary)

    df_summary.to_csv("milvus_lite_summary.csv", index=False)
    df_detail.to_csv("milvus_lite_detail.csv", index=False)

    return df_summary, df_detail


if __name__ == "__main__":
    run_benchmark()