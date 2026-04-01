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
    
    if retriever is None:
        # heuristik murah: keyword RAG
        if any(k in query.lower() for k in ["prospektus", "saham", "laporan", "risiko"]):
            print("🧠 Loading RAG engine...")
            from RAG.rag_setup import setup_rag
            retriever = setup_rag()
            print("✅ RAG loaded")
            
    answer = langchain_router(query, retriever, model)
    print("Bot:", answer)

# INIT RAG
# retriever = setup_rag()

# print("\n🔍 DEBUG: Testing retriever untuk query 'kantor pusat'")
# retrieved_docs = retriever.invoke("kantor pusat")

# for d in retrieved_docs:
#     print("\n----- CHUNK -----")
#     print("HALAMAN:", d.metadata.get("page"))
#     print(d.page_content[:400], "...")
#     print("-----------------\n")

# print("🔥 DEBUG DONE — lanjut chatbot…\n")

# print("🔥 AI Stock Assistant ready!")
# print("Ketik 'exit' untuk keluar.\n")

# while True:
#     query = input("User: ")
    
#     if query == "exit":
#         break

#     answer = langchain_router(query, retriever, model)
#     print("Bot:", answer)