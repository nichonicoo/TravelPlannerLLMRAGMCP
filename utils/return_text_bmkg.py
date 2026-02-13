from LLM.test_lmstudio import local_llm_chat

def return_weather_beautifier(query: str) -> bool:
    messages = f"""
                    Kamu adalah asisten cuaca yang ramah dan informatif.

                    Gunakan data resmi dari BMKG di bawah ini untuk menjelaskan
                    kondisi cuaca dengan bahasa manusia yang alami, mudah dipahami,
                    dan relevan untuk aktivitas sehari-hari.

                    Anggap ini adalah LANJUTAN percakapan.
                    JANGAN membuka jawaban dengan salam, sapaan, atau basa-basi
                    (seperti "Halo", "Selamat pagi", dsb).

                    Sumber data: BMKG

                    DATA CUACA (FAKTA):
                    {query}

                    ATURAN PENJELASAN:
                    1. Awali dengan ringkasan kondisi cuaca hari ini di wilayah tersebut.
                    2. Jelaskan kondisi pagi, siang/sore, dan malam secara wajar.
                    3. Sebutkan suhu dan kelembapan dengan bahasa naratif.
                    4. Berikan rekomendasi pakaian dan perlengkapan.
                    5. Tutup dengan saran singkat untuk aktivitas luar ruangan.
                    6. Jangan menampilkan data mentah atau JSON.

                    TULIS JAWABAN AKHIR:
                    """

    answer = local_llm_chat(messages, temperature= 0)

    if not answer:
        return False

    return answer
