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
        if session.get("origin_city"):
            session_context += f"\n- Kota asal sebelumnya: {session['origin_city']}"
        if session.get("destination_city"):
            session_context += f"\n- Kota tujuan sebelumnya: {session['destination_city']}"
        if session.get("origin_iata"):
            session_context += f"\n- Departure ID: {session['origin_iata']}"
        if session.get("destination_iata"):
            session_context += f"\n- Arrival ID: {session['destination_iata']}"
            # params["arrival_id"] = session["destination_iata"]

    print('session_context: ', session_context)

    prompt = f"""Ekstrak parameter penerbangan dari query user berikut.
                    Balas HANYA dalam format JSON, tanpa penjelasan, tanpa backtick.
                    
                    Aturan:
                    - JANGAN mengisi departure_id atau arrival_id. Gunakan departure id dan arrival id dari Konteks
                    - departure_date: format YYYY-MM-DD. Jika tidak disebutkan, gunakan {tomorrow}
                    - return_date: format YYYY-MM-DD jika round trip, None jika one way
                    - type: Format angka. Jika return_date tidak disebutkan maka (2), Jika return_date ada maka (1)
                    - adults: jumlah penumpang, default 1
                    - children: jika ada maka tambahkan, jika tidak ada maka default None, 
                    - infants_in_seat: jika ada maka tambahkan, jika tidak ada maka default None, 
                    - infants_on_lap: jika ada maka tambahkan, jika tidak ada maka default None,
                    - Jika user tidak ada batasan harga, set max_price menjadi null, jika ada maka buat dengan format angka  = 970000 (Sembilan Ratus tujuh puluh ribu)
                    - travel_class: Jawab dengan nomor dengan urutan seperti (1 Ekonomi), (2 Premium Economy), (3 Business), (4 First)
                    - Jika sama sekali tidak bisa ditentukan, isi null
                    - Currency ditentukan dengan bahasa apa yang diberikan oleh user. Jika user berbicara dengan bahasa indonesia maka IDR jika user berbicara dengan bahasa inggris maka USD 
                    
                    Konteks sesi saat ini:{session_context if session_context else " (tidak ada)"}
                    Hari ini: {today}
                    
                    Query: "{query}"
                    
                    Contoh Format output:
                    {{
                    "departure_id": "CGK",
                    "arrival_id": "MLG",
                    "type": "1" Jika return_date tidak disebutkan maka (2 One Way), Jika return_date ada maka (1 Round Trip),
                    "outbound_date": "2025-08-01",
                    "return_date": None / selalu lebih besar dari outbound_date,
                    "adults": 1,
                    "children": None, 
                    "max_price": None, 
                    "travel_class": "1",
                    "currency: "IDR"
                    }}"""

    print('prompting: ', prompt)

    answer = chat(prompt, temperature=0)
    print('asnwer dari flight param: ', answer)
    if not answer:
        return None

    try:
        clean = re.sub(r"```.*?```", "", answer, flags=re.DOTALL).strip()
        clean = re.sub(r"```", "", clean).strip()
        params = json.loads(clean)

        if not params.get("departure_id") or not params.get("arrival_id"):
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
    required = ["departure_id", "arrival_id", "currency"]
    return [k for k in required if not params.get(k)]
