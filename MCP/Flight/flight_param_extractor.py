# to convert from Jakarta -> CGK 
import json
import re
from LLM.qwen import chat
from datetime import date, timedelta

def extract_flight_param(query: str, session: dict = None) -> dict | None:
    """
    Ekstrak origin, destination, departure_date, return_date, adults, travel_class.
    Pakai session untuk konteks (last_city, last_origin).
 
    Return dict params atau None kalau gagal.
    """
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    session_context = ""
    
    if session: 
        if session.get("last_city_iata"):
            session_context += f"\n- Kota tujuan dari konteks sebelumnya: {session['last_city_name']} ({session['last_city_iata']})"
        
        if session.get("last_origin"):
            session_context += f"\n- Kota asal dari konteks sebelumnya: {session['last_origin']}"
            
    prompt = f"""Ekstrak parameter penerbangan dari query user berikut.
                    Balas HANYA dalam format JSON, tanpa penjelasan, tanpa backtick.
                    
                    Aturan:
                    - origin dan destination: kode IATA 3 huruf (CGK, DPS, SUB, dll)
                    - departure_date: format YYYY-MM-DD. Jika tidak disebutkan, gunakan {tomorrow}
                    - return_date: format YYYY-MM-DD jika round trip, null jika one way
                    - adults: jumlah penumpang, default 1
                    - travel_class: ECONOMY / BUSINESS / FIRST, default ECONOMY
                    - Jika origin tidak jelas dan ada konteks, gunakan konteks
                    - Jika destination tidak jelas dan ada konteks, gunakan konteks
                    - Jika sama sekali tidak bisa ditentukan, isi null
                    - Currency ditentukan dengan bahasa apa yang diberikan
                    
                    Konteks sesi saat ini:{session_context if session_context else " (tidak ada)"}
                    Hari ini: {today}
                    
                    Query: "{query}"
                    
                    Format output:
                    {{
                    "origin": "CGK",
                    "destination": "DPS",
                    "departure_date": "2025-08-01",
                    "return_date": null,
                    "adults": 1,
                    "travel_class": "ECONOMY",
                    "currencyCode: "IDR"
                    }}"""
                    
    answer = chat(prompt, temperature= 0)
    if not answer:
        return None
        
    try: 
        clean = re.sub(r"```.*?```", "", answer, flags=re.DOTALL).strip()
        clean = re.sub(r"```", "", clean).strip()
        params = json.loads(clean)
            
        if not params.get("origin") or not params.get("destination"):
            print(f"[FlightParams] origin/destination kosong: {params}")
            return None
            
        return params
        
    except json.JSONDecodeError as e:
        print(f"[FlightParams] JSON parse error: {e}\nRaw: {answer}")
        return None
        
def missing_params(params: dict) -> list[str]:
    """
    Cek parameter apa yang masih kurang.
    Return list nama param yang null/kosong.
    """
    required = ["origin", "destination", "departure_date"]
    return [k for k in required if not params.get(k)] 