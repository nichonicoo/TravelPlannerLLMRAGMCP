from LLM.test_lmstudio import local_llm_chat

def decision_routing(query: str) -> str:
    messages = f"""
            Klasifikasikan intent user ke salah satu:
            - MCP = cuaca 
            - RAG = dokumen, laporan, saham, prospektus
            - LLM = ngobrol umum / opini / penjelasan, kondisi saat ini 

            Balas SATU kata saja: MCP, RAG, atau LLM.

            User query:
            {query}
            """

    answer = local_llm_chat(messages, temperature= 0)

    if not answer:
        return "LLM"
    
    answer = answer.strip().upper()
    
    if answer not in["MCP", "RAG", "LLM"]:
        return "LLM"

    return answer
