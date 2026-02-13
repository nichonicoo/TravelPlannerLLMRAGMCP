def run_rag(query, retriever, gemini):
    # Step 1 — Retrieve relevant documents
    docs = retriever.invoke(query)

    # Build context with page numbers
    context = ""
    for d in docs:
        page = d.metadata.get("page", "unknown")
        text = d.page_content.strip()
        if len(text) > 10:
            context += f"[HALAMAN {page}]\n{text}\n\n"

    # Step 2 — Gemini stage 1: Extract only the info needed
    extraction_prompt = f"""
Berikut adalah potongan teks dari dokumen prospektus perusahaan.
Tugasmu adalah MENGELOLA informasi berikut, tanpa menambah hal baru.

--- CONTEXT ---
{context}
----------------

INSTRUKSI:
- Temukan informasi yang relevan dengan pertanyaan.
- Jika ada halaman yang isinya tidak relevan, abaikan.
- Jika tidak ada informasi terkait, jawab: "NO_DATA".

PERTANYAAN:
{query}

JAWAB HANYA DENGAN JSON Valid:
{{
  "status": "ok" atau "NO_DATA",
  "relevant_text": "teks asli yang relevan",
  "pages": [list halaman relevan]
}}
"""

    extract = gemini.generate_content(extraction_prompt).text

    # If no info found → early exit
    if "NO_DATA" in extract:
        return "Informasi tidak tersedia di dokumen."

    # Step 3 — Gemini step 2: Final reasoning answer
    final_prompt = f"""
Gunakan informasi berikut untuk menyusun jawaban final.

INFORMASI TERPILIH:
{extract}

PERTANYAAN:
{query}

ATURAN:
- Jangan halusinasi.
- Gunakan hanya informasi di atas.
- Format jawaban jelas dan ringkas.
- Cantumkan halaman jika tersedia.

JAWABAN FINAL:
"""
    response = gemini.generate_content(final_prompt)
    return response.text
