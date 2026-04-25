import json
from app.infrastructure.llm.base import LLMProvider


def decision_routing(query: str, llm: LLMProvider) -> str:
    # messages = f"""
    #         Klasifikasikan intent user ke salah satu:
    #         - MCP = cuaca
    #         - RAG = dokumen, laporan, saham, prospektus
    #         - LLM = ngobrol umum / opini / penjelasan, kondisi saat ini

    #         Balas SATU kata saja: MCP, RAG, atau LLM.

    #         User query:
    #         {query}
    #         """

    prompting = f"""Kamu adalah orchestrator Travel Assistant.
                Klasifikasikan intent user ke salah satu:

                - WEATHER  → cuaca, hujan, suhu, prakiraan, panas, dingin
                - FLIGHT   → tiket pesawat, jadwal penerbangan, harga flight
                - HOTEL   → hotel, penginapan, stay, resort, villa, tempat menginap
                - RAG      → pertanyaan berbasis informasi/pengetahuan (contoh: sejarah tempat wisata, kapan dibangun, fakta destinasi, dll)
                - LLM      → wisata, kuliner, rekomendasi tempat, obrolan umum

                Balas SATU kata saja: WEATHER, FLIGHT, HOTEL, RAG, atau LLM.

                Query: {query}"""

    answer = llm.generate(prompting)
    if not answer:
        return "LLM"
    answer = answer.strip().upper()
    if answer not in ["WEATHER", "FLIGHT", "HOTEL", "RAG", "LLM"]:
        return "LLM"

    return answer


def reference_prev_locations(query: str, llm: LLMProvider) -> bool:
    # function for cek apakah ini merujuk ke lokasi yg tadi di bicarakan
    prompting = f"""Apakah kalimat ini menggunakan kata ganti seperti
                "di situ", "ke sana", "di sana", "ke situ", "di tempat itu",
                atau merujuk ke lokasi yang sudah disebutkan sebelumnya?

                Jawab HANYA: YA atau TIDAK.

                Kalimat: "{query}"
                """
    answer = llm.generate(prompting)
    if not answer:
        return False

    return answer.strip().upper().startswith("YA")


def extract_city(query: str, llm: LLMProvider) -> dict | None:
    prompt = f"""Ekstrak nama kota (origin) atau lokasi wisata (destination) dari kalimat berikut.
            Balas HANYA JSON: {{"origin": "nama", "destination": "nama"}}
            Jika tidak ada, balas: None

            Contoh:
            - "ada apa di malang?" → {{"origin": None, "destination": "Malang"}}
            - "cuaca hari ini?" → {{"origin": None, "destination": None}}
            - "tiket ke bali" → Bali
            - "Berapa harga tiket dari jakarta ke bali ?" -> {{"origin": "Jakarta", "destination": "Bali"}}
            - "tiket ke bali dari jakarta" -> {{"origin": "Jakarta", "destination": "Bali"}}
            - "terbang ke malang" -> {{"origin": null, "destination": "Malang"}}

            Kalimat: "{query}"
             
            """
    answer = llm.generate(prompt)

    if not answer or "NONE" in answer.upper():
        return None

    try:
        # Mengubah string JSON dari LLM menjadi Dictionary Python
        return json.loads(answer)
    except Exception as e:
        print(f"[LLM Error] Gagal parse JSON: {e}")
        return None

    # if not answer:
    #     return None
    # answer = answer.strip()
    # return None if answer.upper() == "NONE" else answer
