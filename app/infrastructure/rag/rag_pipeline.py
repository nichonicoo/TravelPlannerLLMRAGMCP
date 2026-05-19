import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


class RAGEngine:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(
            os.path.join(self.base_dir, "../../../"))

        self.doc_path = os.path.join(self.base_dir, "documents")
        self.db_path = os.path.join(self.project_root, "data", "chroma_db")

        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        self.vector_db = self._init_vector_db()

    def _init_vector_db(self):
        print("DB_PATH:", self.db_path)
        print("DOC_PATH:", self.doc_path)

        # kalau DB sudah ada
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            print("--- Load Vector DB ---")
            return Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )

        print("--- Creating Vector DB ---")

        loader = DirectoryLoader(
            self.doc_path,
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
            embedding=self.embeddings,
            persist_directory=self.db_path
        )

        print(f"Chunks created: {len(chunks)}")
        return db

    def retrieve_context(self, query, k=4):
        docs = self.vector_db.similarity_search(query, k=k)

        if not docs:
            return ""

        # return "\n\n".join([
        #     f"[SOURCE: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        #     for doc in docs
        # ])

        return "\n\n".join([doc.page_content for doc in docs])

    def build_prompt(self, context, query):
        return f"""
Anda adalah asisten pariwisata Indonesia.
Jawab hanya berdasarkan data.

Jika tidak ada dalam data, jawab: "Saya tidak tahu."

DATA:
{context}

PERTANYAAN:
{query}

JAWABAN:
"""
