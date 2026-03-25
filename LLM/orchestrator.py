from LLM.qwen import chat
import pandas as pd 
from difflib import get_close_matches
import re
import os

def decision_routing(query: str) -> str:
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
                - RAG      → dokumen, prospektus, laporan keuangan, saham
                - LLM      → wisata, kuliner, rekomendasi tempat, obrolan umum

                Balas SATU kata saja: WEATHER, FLIGHT, RAG, atau LLM.

                Query: {query}"""

    answer = chat(prompting, temperature= 0)
    if not answer:
        return "LLM"
    answer = answer.strip().upper()
    if answer not in["WEATHER", "FLIGHT", "RAG", "LLM"]:
        return "LLM"

    return answer

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

    answer = chat(messages, temperature= 0)

    if not answer:
        return False

    return answer

def reference_prev_locations(query: str) -> bool:
    # function for cek apakah ini merujuk ke lokasi yg tadi di bicarakan 
    prompting = f"""Apakah kalimat ini menggunakan kata ganti seperti
                "di situ", "ke sana", "di sana", "ke situ", "di tempat itu",
                atau merujuk ke lokasi yang sudah disebutkan sebelumnya?

                Jawab HANYA: YA atau TIDAK.

                Kalimat: "{query}"
                """
    answer = chat(prompting, temperature= 0)
    if not answer:
        return False

    return answer.strip().upper().startswith("YA")

def build_carrier_code_index() -> dict: 
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "carriers.csv")
    csv_path = os.path.normpath(csv_path)
    
    try: 
        df = pd.read_csv(csv_path)
        return {
            str(row["Code"]).strip().upper(): str(row["Description"]).strip()
            for _, row in df.iterrows()
            if pd.notna(row["Code"]) and pd.notna(row["Description"])
        }
    except Exception as e: 
        print(f"[CarrierResolver] Gagal load CSV: {e}")
        return {}

carrier_index = build_carrier_code_index()

CARRIER_ALIASES = {
    # Indonesia
    "GA": "Garuda Indonesia",
    "JT": "Lion Air",
    "ID": "Batik Air",
    "QG": "Citilink",
    "IW": "Wings Air",
    "SJ": "Sriwijaya Air",
    "IN": "Nam Air",
    "3N": "TransNusa",
    "XN": "Super Air Jet",
    "XT": "Indonesia AirAsia Extra",
    # Regional Asia
    "AK": "AirAsia",
    "FD": "Thai AirAsia",
    "D7": "AirAsia X",
    "QZ": "Indonesia AirAsia",
    "3K": "Jetstar Asia",
    "TR": "Scoot",
    "SQ": "Singapore Airlines",
    "MH": "Malaysia Airlines",
    "TG": "Thai Airways",
    "CX": "Cathay Pacific",
    "PR": "Philippine Airlines",
    "5J": "Cebu Pacific",
    # Internasional umum
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "EY": "Etihad Airways",
    "KL": "KLM",
    "AF": "Air France",
    "LH": "Lufthansa",
    "BA": "British Airways",
    "JL": "Japan Airlines",
    "NH": "ANA",
    "CZ": "China Southern",
    "MU": "China Eastern",
    "CA": "Air China",
}

def get_carrier_name(code: str) -> str: 
    if not code: 
        return "-"
    
    code = code.strip().upper()
    
    if code in carrier_index:
        return carrier_index[code]
    
    if code in CARRIER_ALIASES: 
        print('ini:')
        return CARRIER_ALIASES[code]
    
    print('code airlines: {code}')
    
    return code

def add_carrier_names(offers: list) -> list: 
    """
    Tambahkan airline_name ke setiap segment dalam offers.
    Dipanggil setelah parsing_offer() di flight_search.py.
    """
    for offer in offers:
        if "error" in offer:
            continue
        for itin in offer.get("itineraries", []):
            for seg in itin.get("segments", []):
                code = seg.get("airline", "-")
                seg["airline_name"] = get_carrier_name(code)
    return offers
    
def _build_iata_index() -> dict:
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "airport-codes.csv")
    csv_path = os.path.normpath(csv_path)
 
    try:
        df = pd.read_csv(csv_path)
        df = df[
            # (df["iso_country"] == "ID") &
            (df["iata_code"].notna()) &
            (df["iata_code"] != "") &
            (~df["name"].str.contains("UNUSABLE|Closed", case=False, na=False))
        ].copy()
 
        # sort from large
        type_order = {"large_airport": 0, 
                      "medium_airport": 1, 
                      "small_airport": 2}
        df["_order"] = df["type"].map(type_order).fillna(3)
        df = df.sort_values("_order")
 
        index = {}
        for _, row in df.iterrows():
            municipality = str(row["municipality"]).lower().strip()
            iata = str(row["iata_code"]).strip()
            short = municipality.split(",")[0].split("-")[0].strip()
            if short and short not in index:
                index[short] = iata
            if municipality not in index:
                index[municipality] = iata
 
        ALIASES = {
            "malang": "MLG",
            "bali": "DPS", "denpasar": "DPS",
            "jogja": "JOG", "yogya": "JOG",
            "lombok": "LOP",
            "medan": "KNO",
            "pekanbaru": "PKU",
            "padang": "PDG",
            "palembang": "PLM",
            "kupang": "KOE",
            "jayapura": "DJJ",
            "ambon": "AMQ",
            "banjarmasin": "BDJ",
        }
        for alias, iata in ALIASES.items():
            if alias not in index:
                index[alias] = iata

        # df.to_csv('output_filtered.csv')
        return index
 
    except Exception as e:
        print(f"[IATA Index] Gagal load CSV: {e}")
        return {}
 
IATA_INDEX = _build_iata_index()

def city_to_iata(city_name: str) -> str | None:
    
    key_city =  city_name.lower().strip()
    print('city to iata -> ', key_city)
    
    if key_city in IATA_INDEX:
        return IATA_INDEX[key_city]
    
    matches = get_close_matches(key_city, IATA_INDEX.keys(),n=1, cutoff= 0.7)
    print('if matches', matches)
    
    if matches: 
        print(f"[IATA] Fuzzy match: '{key_city}' → '{matches[0]}' ({IATA_INDEX[matches[0]]})")
        return IATA_INDEX[matches[0]]
    
    # fallback kalo ga ada
    print(f"[IATA] Tidak ditemukan di CSV, tanya Qwen untuk: {city_name}")
    
    prompt = f"""Apa kode IATA bandara utama di kota "{city_name}" Indonesia?
            Balas HANYA 3 huruf kode IATA. Jika tidak tahu, balas: NONE"""
            
    answer = chat(prompt, temperature=0)
    
    if not answer: 
        return None
    
    answer = answer.strip().upper()
    
    return None if answer == 'None' or len(answer) != 3 else answer

def extract_city(query: str) -> str | None:
    prompt = f"""Ekstrak nama kota atau lokasi wisata dari kalimat berikut.
            Jika ada lokasi, balas HANYA nama kotanya (1-3 kata).
            Jika tidak ada, balas: NONE

            Contoh:
            - "ada apa di malang?" → Malang
            - "cuaca hari ini?" → NONE
            - "tiket ke bali" → Bali

            Kalimat: "{query}"
            
            Jika kamu 
            """
    answer = chat(prompt, temperature=0)
    if not answer:
        return None
    answer = answer.strip()
    return None if answer.upper() == "NONE" else answer
        
    
