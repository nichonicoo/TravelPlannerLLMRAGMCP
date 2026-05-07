import os

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, "../../../"))
print("base_dir:", base_dir)
print("project_root:", project_root)

doc_path = os.path.join(base_dir, "documents")
db_path = os.path.join(project_root, "data", "chroma_db")
print("doc_path:", doc_path)
print("db_path:", db_path)
