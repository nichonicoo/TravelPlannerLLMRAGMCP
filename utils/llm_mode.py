from LLM.qwen import chat

def LLM_answering(query: str) -> str:
    messages = f"""
            Kamu adalah Travel Agent profesional di Indonesia.

            Tugas kamu:
            - Menjawab pertanyaan tentang wisata, tempat menarik, kuliner, dan aktivitas.
            - Berikan jawaban singkat, jelas, dan informatif.
            - Gunakan bahasa Indonesia yang natural.
            - Maksimal 70 kalimat.
            - Jangan bertele-tele.
            - Jangan memberikan informasi di luar konteks pertanyaan.
            - Be Friendly!

            Query User:
            {query}

            Jawaban:
            """
    
    answer = chat(messages, temperature= 0)

    return answer
