from LLM.qwen import chat
import re
from datetime import datetime as q

def format_duration(iso_duration: str) -> str:
    """
    Convert ISO 8601 duration ke format manusia.
    PT2H30M → 2j 30m
    """
    h = re.search(r"(\d+)H", iso_duration)
    m = re.search(r"(\d+)M", iso_duration)
    parts = []
    if h:
        parts.append(f"{h.group(1)}j")
    if m:
        parts.append(f"{m.group(1)}m")
    return " ".join(parts) if parts else iso_duration

def format_datetime(datetime: str) -> str:
    # 2025-08-01T07:30:00 → 01 Agt 07:30
    
    try: 
        dt = q.fromisoformat(datetime)
        months = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"]
        
        return f"{dt.day:02d} {months[dt.month-1]} {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return datetime

def format_idr(price_raw):
    """Mengubah 1000000 menjadi 1.000.000"""
    try:
        if price_raw == '-' or price_raw is None:
            return "N/A"
        # Format ke ribuan dengan koma dulu, lalu tukar koma jadi titik
        value = int(float(price_raw))
        return f"IDR {value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"IDR {price_raw}"
    
def build_offer_text(offers: list, trip_type: str) -> str: 
    print(offers)
    lines = []
    for i, o in enumerate(offers, 1):
        price_raw = o.get('price_idr', '-')
        # try:
        #     price = f"IDR {int(float(price_raw)):,}" if price_raw != '-' else "N/A"
        # except (ValueError, TypeError):
        #     price = f"IDR {price_raw}"
        price = format_idr(price_raw)
        
        cabin = o.get("cabin", "-")
        baggage = o.get("baggage", "-")
        
        itin_lines = []
        
        for leg_idx, itin in enumerate(o.get("itineraries", [])):
            label = "Pergi" if leg_idx == 0 else "Pulang" 
            duration = format_duration(itin.get("duration", "-"))
            stops = itin.get("stops", 0)
            stop_label = "Langsung" if stops == 0 else f"{stops}x transit"
            
            segs = itin.get("segments", [])
            
            if segs: 
                first = segs[0]
                last = segs[-1]
                dep = format_datetime(first.get("departure_time", "-"))
                arr = format_datetime(last.get("arrival_time", "-"))
                airline = first.get("airline_name") or first.get("airline", "-")
                flight_no = " → ".join(s.get("flight_number", "") for s in segs)
                
                itin_lines.append(
                    f"  [{label}] {airline} {flight_no} | {dep} → {arr} | {duration} | {stop_label}"
                )
                
        lines.append(
            f"Opsi {i}: {price} | {cabin} | Bagasi: {baggage}\n" + "\n".join(itin_lines)
        )
        
    return "\n\n".join(lines)     

# def carrier_code(result: dict) -> str: 
    

def beautify_flight_offerst(result: dict) -> str: 
    if result["status"] == "NOT_FOUND":
        return "Maaf, tidak ada penerbangan tersedia untuk rute dan tanggal tersebut."
    if result["status"] == "ERROR":
        return f"Terjadi kesalahan: {result.get('message', 'unknown error')}"   
    
    offers = result.get("offers", [])
    trip_type = result.get("trip_type", "one_way")
    origin = result.get("origin", "-")
    destination = result.get("destination", "-")
    dep_date = result.get("departure_date", "-")
    ret_date = result.get("return_date")
    adults = result.get("adults", 1)
    
    offer_text = build_offer_text(offers, trip_type)
    
    trip_label = "Pulang-pergi" if trip_type == "round_trip" else "Sekali jalan"
    date_label = f"{dep_date}" + (f" → {ret_date}" if ret_date else "")
    
    prompt = f"""Kamu adalah travel agent yang membantu mencari tiket pesawat.
                Sajikan hasil pencarian penerbangan berikut dengan bahasa Indonesia yang ramah, ringkas, dan mudah dipahami.
                
                Info perjalanan:
                - Rute: {origin} → {destination}
                - Tanggal: {date_label}
                - Tipe: {trip_label}
                - Penumpang: {adults} orang
                
                Hasil penerbangan yang tersedia:
                {offer_text}
                
                Panduan:
                - Tampilkan semua opsi dengan jelas
                - Sebutkan maskapai, nomor penerbangan, jam berangkat & tiba, durasi, jumlah transit, harga, dan info bagasi
                - Gunakan format yang mudah dibaca, boleh pakai bullet atau nomor
                - Tutup dengan kalimat singkat yang membantu user memilih
                - JANGAN tambah info yang tidak ada di data
                
                JAWABAN:"""
    answer = chat(prompt, temperature= 0.2)
    
    return answer or offer_text
        
    
    