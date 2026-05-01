# from RAG.rag_setup import setup_rag
from LLM.gemini_model import model
# from router.langchain_router import langchain_router
from router.router import langchain_router

retriever = None 

print("🔥 Ready!")
print("Ketik 'exit' untuk keluar.\n")

while True: 
    query = input("user: ")
    
    if query == 'exit':
        break
            
    answer = langchain_router(query, retriever)
    print("Bot:", answer)
