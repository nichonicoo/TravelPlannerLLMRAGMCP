import os, sys

# biar bisa import dari root project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "chroma_db")
DOC_PATH = os.path.join(BASE_DIR, "documents")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
    # kalau error torch, ganti:
    # model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def init_vector_db():
    print("DB_PATH:", DB_PATH)
    print("DOC_PATH:", DOC_PATH)

    # kalau DB sudah ada
    if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
        print("--- Load Vector DB ---")
        return Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings
        )

    print("--- Creating Vector DB ---")

    loader = DirectoryLoader(
        DOC_PATH,
        glob="*.txt",
        loader_cls=lambda path: TextLoader(path, encoding="utf-8")
    )

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(docs)

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    print(f"Chunks created: {len(chunks)}")
    return db

def retrieve_context(vector_db, query, k=4):
    docs = vector_db.similarity_search(query, k=k)

    if not docs:
        return ""

    return "\n\n".join([
        f"[SOURCE: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    ])

def build_prompt(context, query):
    return [
        {
            "role": "system",
            "content": "Anda adalah asisten pariwisata Indonesia. Jawab hanya berdasarkan data. Jika tidak ada dalam data, jawab: 'Saya tidak tahu.'"
        },
        {
            "role": "user", 
            "content": f"DATA:\n{context}\n\nPERTANYAAN:\n{query}\n\nJawab:"
        }
    ]
