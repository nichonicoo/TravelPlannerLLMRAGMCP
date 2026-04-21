from MCP.Hotel.hotel_search import search_hotel
from MCP.Hotel.hotel_beautifier import (
    
    beautify_hotels,
    beautify_hotel_detail
)
from MCP.Hotel.hotel_param_extractor import extract_hotel_params

from LLM.qwen import chat
import router.sessions as session
import json
import re

def is_detail_request_llm(query: str) -> bool:
    prompt = f"""
    Apakah user ingin melihat detail hotel dari hasil sebelumnya?

    Jawab HANYA: YA atau TIDAK

    Query: "{query}"
    """

    answer = chat(prompt, temperature=0)

    if not answer:
        return False

    return answer.strip().upper().startswith("YA")

#extract hotels for details
def extract_index_llm(query: str) -> int | None:
    prompt = f"""
    Dari kalimat berikut, ambil nomor hotel yang dimaksud user.

    Balas HANYA JSON:
    {{"index": angka}}

    Jika tidak ada:
    {{"index": null}}

    Query: "{query}"
    """

    answer = chat(prompt, temperature=0)

    if not answer:
        return None

    try:
        data = json.loads(answer)
        idx = data.get("index")
        return int(idx) - 1 if idx else None
    except:
        return None

def extract_index_fallback(query: str):
    match = re.search(r"\d+", query)
    return int(match.group()) - 1 if match else None

def hotel_handler(query: str, session_data: dict = None):
    
    if session_data is None:
        session_data = {}
        
    last_hotels = session_data.get("last_hotels", [])

    # DETAIL MODE
    if is_detail_request_llm(query) and last_hotels:

        idx = extract_index_llm(query)

        if idx is None:
            idx = extract_index_fallback(query)

        if idx is None or idx >= len(last_hotels):
            return {
                "status": "ERROR",
                "message": "Hotel tidak ditemukan dari pilihan sebelumnya."
            }

        token = last_hotels[idx]["token"]

        result = search_hotel({
            "property_token": token
        })

        return {
            "status": "OK",
            "data": beautify_hotel_detail(result)
        }

    # SEARCH MODE
    params = extract_hotel_params(query, session_data)
    print("Extracted hotel params: ", params)
    print("Location Data ", params.get("location"))
    if not params.get("location"):
        return {
            "status": "NEED_INFO",
            "message": "Mau cari hotel di kota mana?"
        }

    result = search_hotel(params)

    if result["status"] != "OK":
        return result

    # save ke session
    session.update_hotels([
        {
            "name": h.get("name"),
            "token": h.get("property_token")
        }
        for h in result.get("properties", [])[:5]
    ])

    return {
        "status": "OK",
        "data": beautify_hotels(result)
    }