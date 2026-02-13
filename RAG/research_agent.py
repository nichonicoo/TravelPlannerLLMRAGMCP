#Ini agent yang kamu minta:
#   RAG ambil potongan teks + halaman
#   Gemini tahap 1: pilih teks yang relevan
#   Gemini tahap 2: susun jawaban final yang rapi

# RAG/research_agent.py

def run_research_agent(query, retriever, gemini):
    # ---------- STEP 1: RETRIEVE ----------
    docs = retriever.invoke(query)

    if not docs:
        return "Informasi tidak tersedia di dokumen."

    # Bangun context, sertakan metadata halaman
    context = ""
    for d in docs:
        page = d.metadata.get("page", "unknown")
        text = d.page_content.strip()
        if len(text) > 10:
            context += f"[HALAMAN {page}]\n{text}\n\n"

    if not context.strip():
        return "Informasi tidak tersedia di dokumen."

    # ---------- STEP 2: GEMINI – EKSTRAK INFO RELEVAN ----------
    extraction_prompt = f"""
Kamu adalah Equity Research Assistant yang mengolah prospektus saham.

Berikut adalah potongan teks dari dokumen prospektus.
Tugasmu sekarang: PILIH teks yang benar-benar relevan dengan pertanyaan.

--- CONTEXT ---
{context}
----------------

INSTRUKSI:
- Cari bagian teks yang menjawab pertanyaan user.
- Jika sebuah potongan teks tidak relevan, abaikan.
- Jika tidak ada teks yang relevan sama sekali, jawab: "NO_DATA".
- Jika ada, salin teks yang relevan apa adanya (jangan diringkas sendiri).
- Jika tahu halamannya dari tag [HALAMAN X], masukkan ke daftar halaman.

PERTANYAAN:
{query}

JAWAB HANYA DENGAN JSON VALID seperti ini (tanpa penjelasan lain):
{{
  "status": "ok" atau "NO_DATA",
  "relevant_text": "teks asli yang relevan",
  "pages": [daftar nomor halaman unik, misal: [37, 38]]
}}
"""

    extract_raw = gemini.generate_content(extraction_prompt).text or ""

    # Kalau Gemini bilang NO_DATA → stop di sini
    if "NO_DATA" in extract_raw:
        return "Informasi tidak tersedia di dokumen."

    # ---------- STEP 3: GEMINI – FINAL REASONING ----------
    final_prompt = f"""
Kamu adalah Equity Research Analyst.

Gunakan informasi berikut untuk menyusun jawaban final
terkait pertanyaan user.

INFORMASI TERSTRUKTUR (JSON):
{extract_raw}

PERTANYAAN:
{query}

ATURAN:
- Jangan mengarang di luar informasi yang ada pada JSON di atas.
- Jika ada field "pages", gunakan untuk menyebutkan halaman.
- Jelaskan dengan bahasa yang jelas, ringkas, dan profesional.
- Jika tetap tidak ada jawaban pasti, jelaskan bahwa detail
  tersebut tidak eksplisit disebut di prospektus.

JAWABAN FINAL:
"""

    final_response = gemini.generate_content(final_prompt)
    return final_response.text
