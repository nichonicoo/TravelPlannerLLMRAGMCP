from LLM.qwen import chat

def reference_prev_locations(query: str) -> bool:
    messages = f"""
            Jawab HANYA dengan YA atau TIDAK.

            Apakah kalimat berikut MERUJUK ke lokasi
            yang telah disebutkan sebelumnya dalam percakapan?

            Kalimat:
            "{query}"
            """

    answer = chat(messages, temperature= 0)

    if not answer:
        return False

    return answer.strip().upper().startswith("YA")
