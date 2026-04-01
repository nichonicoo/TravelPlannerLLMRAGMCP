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
    
def render_flight(o):
    flight = o.get("flights", [{}])[0]

    airline = flight.get("airline", "-")
    flight_no = flight.get("flight_number", "-")
    airplane = flight.get("airplane", "-")
    travel_class = flight.get("travel_class", "-")
    legroom = flight.get("legroom")

    dep = flight.get("departure_airport", {}).get("time", "-")
    arr = flight.get("arrival_airport", {}).get("time", "-")
    duration = f"{flight.get('duration', 0)} menit"

    price = format_idr(o.get("price"))

    # 🔧 FIX NEW
    extensions = flight.get("extensions", [])

    baggage = None
    usb = False
    wifi = False

    for e in extensions:
        e_lower = e.lower()

        if "bagasi" in e_lower or "kg" in e_lower:
            baggage = e

        if "usb" in e_lower:
            usb = True

        if "wifi" in e_lower or "stream" in e_lower:
            wifi = True

    # 🔧 carbon emission
    emission = o.get("carbon_emissions", {}).get("this_flight")
    emission_text = f"{int(emission/1000)} kg" if emission else None

    diff = o.get("carbon_emissions", {}).get("difference_percent")

    lines = [
        f"{airline} ({flight_no})",
        f"✈️ {airplane} | {travel_class}",
        f"🕐 {dep} → {arr} ({duration})"
    ]

    if legroom:
        lines.append(f"💺 Legroom: {legroom}")

    if baggage:
        lines.append(f"🧳 {baggage}")

    if usb:
        lines.append("🔌 USB tersedia")

    if wifi:
        lines.append("📡 Bisa streaming / WiFi")

    if emission_text:
        if diff and diff < 0:
            lines.append(f"🌱 Emisi: {emission_text} (lebih rendah dari rata-rata)")
        else:
            lines.append(f"🌱 Emisi: {emission_text}")

    lines.append(f"💰 {price}")

    return "\n".join(lines)

# 🔧 FIX NEW
def build_price_insight(result):
    insights = result.get("price_insights", {})

    if not insights:
        return None

    level = insights.get("price_level")

    if level == "low":
        return "📊 Harga saat ini: murah (di bawah rata-rata)"
    elif level == "typical":
        return "📊 Harga saat ini: normal"
    elif level == "high":
        return "📊 Harga saat ini: mahal (di atas rata-rata)"

    return None
    
# def build_offer_text(offers: list) -> str:
#     lines = []
#     for i, o in enumerate(offers[:5], 1): # Batasi 5 opsi
#         price = format_idr(o.get("price", 0))
        
#         itin_lines = []
#         # SerpApi menaruh detail flight di dalam list 'flights'
#         for flight in o.get("flights", []):
#             airline = flight.get("airline", "-")
#             f_no = flight.get("flight_number", "-")
#             dep_time = flight.get("departure_airport", {}).get("time", "-")
#             arr_time = flight.get("arrival_airport", {}).get("time", "-")
#             duration = f"{flight.get('duration', 0)} menit"
            
#             itin_lines.append(
#                 f"  - {airline} ({f_no}) | {dep_time} -> {arr_time} ({duration})"
#             )
        
#         lines.append(f"Opsi {i}: {price}\n" + "\n".join(itin_lines))
#     return "\n\n".join(lines)

def safe_price(o):
    try:
        p = o.get("price")
        return float(p) if p and float(p) > 0 else float("inf")
    except:
        return float("inf")


def get_duration(o):
    try:
        return o.get("flights", [{}])[0].get("duration", 9999)
    except:
        return 9999
# 🔧 FIX NEW
def build_highlights(offers):
    if not offers:
        return None, None, None

    cheapest = min(offers, key=safe_price)
    fastest = min(offers, key=get_duration)

    # ⭐ best value = balance price & duration
    def score(o):
        return safe_price(o) * 0.7 + get_duration(o) * 1000 * 0.3

    best = min(offers, key=score)

    return cheapest, fastest, best

def build_offer_text(offers: list, origin: str, destination: str, result=None) -> str:
    if not offers:
        return "Maaf, tidak ditemukan penerbangan."

    cheapest, fastest, best = build_highlights(offers)

    lines = [f"✈️ Hasil Penerbangan {origin} → {destination}:\n"]

    # 🔧 FIX NEW
    if result:
        insight = build_price_insight(result)
        if insight:
            lines.append(insight + "\n")

    if cheapest:
        lines.append("🔥 Termurah:")
        lines.append(render_flight(cheapest) + "\n")

    if fastest:
        lines.append("⚡ Tercepat:")
        lines.append(render_flight(fastest) + "\n")

    if best:
        lines.append("⭐ Rekomendasi:")
        lines.append(render_flight(best) + "\n")

    lines.append("──────────────────\n")

    for i, o in enumerate(offers[:5], 1):
        lines.append(f"{i}. {render_flight(o)}\n")

    return "\n".join(lines)
    

def beautify_flight_offerst(result: dict) -> str:
    if result["status"] != "OK":
        return "Maaf, tiket tidak ditemukan atau terjadi kesalahan."

    offers = result.get("offers", [])

    base_text = build_offer_text(
        offers,
        origin=result.get("origin"),
        destination=result.get("destination"),
        result=result
    )

    # 🔧 OPTIONAL LLM LAYER
    prompt = f"""
        Rapikan teks berikut agar lebih natural dan enak dibaca.
        JANGAN mengubah isi data.
        JANGAN menambahkan informasi baru.
        JANGAN berasumsi.

        Gunakan Bahasa Indonesia yang santai dan profesional.

        Teks:
        {base_text}
        """

    response = chat(prompt, temperature=0.2)

    return response or base_text
    # if result["status"] != "OK":
    #     return "Maaf, tiket tidak ditemukan atau terjadi kesalahan."
    
    # offers = result.get("offers", [])
    # offer_summary = build_offer_text(offers)
    
    # prompt = f"""Sajikan hasil pencarian penerbangan ini dengan ramah (Bahasa Indonesia).
    # Rute: {result['origin']} -> {result['destination']}
    # Data:
    # {offer_summary}
    
    # Tampilkan maskapai, jam, dan harga. Jangan bertele-tele."""
    
    # return chat(prompt, temperature=0.2)
        
    
    