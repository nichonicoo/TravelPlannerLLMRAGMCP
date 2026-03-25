from LLM.qwen import chat

def mcp_router(query: str) -> str:
    messages = f"""
                Klasifikasikan request user menjadi salah satu:
                - WEATHER → jika terkait cuaca, hujan, panas, suhu, prakiraan
                - FLIGHT → jika terkait tiket pesawat, penerbangan, jadwal flight

                Balas SATU kata saja: WEATHER atau FLIGHT.

                User query:
                {query}
                """

    answer = chat(messages, temperature=0)

    if not answer:
        return None

    answer = answer.strip().upper()

    if answer not in ["WEATHER", "FLIGHT"]:
        return None

    return answer
