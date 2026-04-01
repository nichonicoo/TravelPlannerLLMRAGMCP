from LLM.qwen import chat
import pandas as pd 
from difflib import get_close_matches
import re
import os
import json

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
                - HOTEL   → hotel, penginapan, stay, resort, villa
                - RAG      → dokumen, prospektus, laporan keuangan, saham
                - LLM      → wisata, kuliner, rekomendasi tempat, obrolan umum

                Balas SATU kata saja: WEATHER, FLIGHT, HOTELS, RAG, atau LLM.

                Query: {query}"""

    answer = chat(prompting, temperature= 0)
    if not answer:
        return "LLM"
    answer = answer.strip().upper()
    if answer not in["WEATHER", "FLIGHT", "HOTEL", "RAG", "LLM"]:
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
            # (df["type"].upper() != ('CLOSED', 'HELIPORT')) 
            (~df["type"].str.upper().isin(['CLOSED', 'HELIPORT'])) & 
            (df["iata_code"].notna()) &
            (df["iata_code"] != "") &
            (df["icao_code"] != None) &
            (df["type"].isin(["large_airport", "medium_airport"]))
            (~df["name"].str.contains("UNUSABLE|Closed", case=False, na=False))
        ].copy()
        
        # print('ini df hasil', df)
 
        # sort from large
        type_order = {"large_airport": 0, 
                      "medium_airport": 1, 
                      "small_airport": 2}
        df["_order"] = df["type"].map(type_order).fillna(3)
        
        # df.to_csv('output_3.csv', index = False)
 
        index = {}
        for _, row in df.iterrows():
            municipality = str(row["municipality"]).lower().strip()
            iata = str(row["iata_code"]).strip()
            short = municipality.split(",")[0].split("-")[0].strip()
            
            def add_to_index(key, code):
                if key not in index:
                    index[key] = []
                if code not in index[key]:
                    index[key].append(code)
                    
            if short and short not in index:
                add_to_index(short, iata)
            if municipality not in index:
                add_to_index(municipality, iata)
 
        ALIASES = {
            "jakarta": ["CGK", "HLP"],
            "malang": ["MLG"],
            "bali": ["DPS"], 
            "denpasar": ["DPS"],
            "jogja": ["YIA"], 
            "yogya": ["YIA"],
            "lombok": ["LOP"],
            "medan": ["KNO"],
            "pekanbaru": ["PKU"],
            "padang": ["PDG"],
            "palembang": ["PLM"],
            "kupang": ["KOE"],
            "jayapura": ["DJJ"],
            "ambon": ["AMQ"],
            "banjarmasin": ["BDJ"],
        }
        for alias, iata in ALIASES.items():
            # if alias not in index:
            #     index[alias] = iata
            if isinstance(iata, str): iata = [iata] # Handle kalau cuma string
            for code in iata:
                add_to_index(alias, code)

        # df.to_csv('output_filtered.csv')
        return index
 
    except Exception as e:
        print(f"[IATA Index] Gagal load CSV: {e}")
        return {}
 
IATA_INDEX = _build_iata_index()

def _build_iata_to_airport_map():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "airport-codes.csv")
    csv_path = os.path.normpath(csv_path)

    try:
        df = pd.read_csv(csv_path)

        df = df[
            (df["iata_code"].notna()) &
            (df["iata_code"] != "") &
            (~df["type"].str.upper().isin(['CLOSED', 'HELIPORT']))
        ]

        mapping = {}

        for _, row in df.iterrows():
            code = str(row["iata_code"]).strip().upper()
            name = str(row["name"]).strip()
            city = str(row["municipality"]).strip()

            mapping[code] = f"{code} — {name} ({city})"

        return mapping

    except Exception as e:
        print(f"[IATA FULL NAME] Error: {e}")
        return {}

IATA_FULLNAME_MAP = _build_iata_to_airport_map()

def get_airport_full_name(iata: str) -> str:
    if not iata:
        return iata

    return IATA_FULLNAME_MAP.get(iata.upper(), iata)

city_example = {
    "origin": "Jakarta",
    "destination": "Malangzzzz"
}

city_example_2 = {
    "origin": None,
    "destination": "Malang"
}

def get_city_fuzzy(name): 
    if not name:
        return None
        
    # Cek langsung di index
    if name in IATA_INDEX:
        return IATA_INDEX[name]
        
    # Kalau ga ada, coba fuzzy match
    matches = get_close_matches(name, IATA_INDEX.keys(), n=1, cutoff=0.7)
    if matches:
        matched_city = matches[0]
        print(f"Fuzzy match: '{name}' -> '{matched_city}'")
        return IATA_INDEX[matched_city]
        
    # Kalau tetap ga ada, kembalikan None sesuai maumu
    return None

PRIORITY_AIRPORTS = {
    "jakarta": ["CGK", "HLP"],
    "bali": ["DPS"],
    "malang": ["MLG"],
    "bandung": ["BDO"]
}

def city_to_iata(city_name: dict) -> dict | None:
    
    if not city_name: 
        return None
    
    origin_raw = city_name.get('origin')
    dest_raw = city_name.get('destination')
    
    city_origin = origin_raw.lower().strip() if origin_raw else None
    city_destination = dest_raw.lower().strip() if dest_raw else None
    
    print('city origin:',city_origin, 'city_destination:', city_destination)
    
    result = {}
    
    if city_origin:
        if city_origin in PRIORITY_AIRPORTS:
            result['origin_iatas'] = PRIORITY_AIRPORTS[city_origin]
        result['origin_iatas'] = get_city_fuzzy(city_origin)
        #IATA_INDEX.get(city_origin, []) if city_origin else None
    if city_destination:
        if city_destination in PRIORITY_AIRPORTS:
            result['destination_iatas'] = PRIORITY_AIRPORTS[city_destination]
        result['destination_iatas'] = get_city_fuzzy(city_destination)
        # IATA_INDEX.get(city_destination, []) if city_destination else None
    
    print(result)
    return result

def extract_city(query: str) -> dict | None:
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
    answer = chat(prompt, temperature=0)
    
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

def city_to_iata_2(city_name: str) -> str | None:
    
    key_city =  city_name.lower().strip()
    print('city to iata -> ', key_city)
    
    if key_city in IATA_INDEX:
        print(IATA_INDEX[key_city])
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

city_to_iata(city_example)

# city_to_iata_2('Jakarta')