from datetime import date, timedelta
from LLM.qwen import chat
import re, json

def extract_location_llm(query: str) -> str | None:
    prompt = f"""
    Ekstrak nama kota atau lokasi dari query berikut.
    Balas HANYA JSON:

    {{"location": "nama_kota"}}

    Jika tidak ada, balas:
    {{"location": null}}

    Query: "{query}"
    """

    answer = chat(prompt, temperature=0)

    if not answer:
        return None

    try:
        data = json.loads(answer)
        return data.get("location")
    except:
        return None

def extract_currency_llm(query: str) -> str | None:
    prompt = f"""
    Ekstrak Currency dari bahasa yang digunakan dalam query berikut.
    Balas HANYA JSON:

    {{"currency": "IDR"}}
    Query: "{query}"
    """

    answer = chat(prompt, temperature=0)

    if not answer:
        return None

    try:
        data = json.loads(answer)
        return data.get("currency")
    except:
        return None

def is_reference_location(query: str) -> bool:
    prompt = f"""
    Apakah kalimat ini merujuk ke lokasi sebelumnya?
    Contoh: "di situ", "di sana", "di tempat itu"

    Jawab: YA atau TIDAK

    Query: "{query}"
    """
    answer = chat(prompt, temperature=0)
    return answer and answer.strip().upper().startswith("YA")

def extract_hotel_params(query: str, session: dict = None)-> dict:
    query_lower = query.lower()

    today = date.today()
    check_in = (today + timedelta(days=1)).isoformat()
    check_out = (today + timedelta(days=2)).isoformat()

    location = extract_location_llm(query)
    currencys = extract_currency_llm(query)

    if not location:
        words = query_lower.split()
        for i, w in enumerate(words):
            if w == "di" and i + 1 < len(words):
                location = words[i + 1]
                break
            
    # handle "di situ"        
    if not location and session and is_reference_location(query):
        location = (
            session.get("last_city_destination_name")
            or session.get("last_city_name")
        )

    # if not location and session and session.get("last_city_name"):
    #     location = session["last_city_name"]
    # fallback session (priority destination)
    if not location and session:
        if session.get("last_city_destination_name"):
            location = session["last_city_destination_name"]
        elif session.get("last_city_name"):
            location = session["last_city_name"]

    
    adults = 1
    match_adult = re.search(r"(\d+)\s*(orang|dewasa)", query_lower)
    if match_adult:
        adults = int(match_adult.group(1))

    children = 0
    match_child = re.search(r"(\d+)\s*anak", query_lower)
    if match_child:
        children = int(match_child.group(1))

    min_price = None
    max_price = None

    if "murah" in query_lower:
        max_price = 500000

    sort_by = 3 if "murah" in query_lower else None

    return {
        "location": location,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "children": children,
        "currency": currencys,
        "sort_by": sort_by,
        "min_price": min_price,
        "max_price": max_price
    } 