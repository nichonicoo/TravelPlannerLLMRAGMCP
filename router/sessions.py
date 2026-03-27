# session manager 
# - Auto-expire konteks setelah EXPIRE_AFTER_N_TURNS turn tidak disebut
# - Smart reset kalau topik non-travel
# - Update otomatis kalau user sebut kota/lokasi baru

EXPIRE_AFTER_N_TURNS = 5

NON_TRAVEL_TOPICS = [
    "fisika", "kimia", "matematika", "sejarah", "politik",
    "relativitas", "ekonomi", "hukum", "kedokteran", "olahraga",
    "teknologi", "programming", "coding", "saham", "investasi"
]

SESSION = {
    # Lokasi
    "last_city_name": None,      # ex: "Malang"
    "last_city_destination_name": None,
    "last_city_iata": None,      # ex: "MLG"
    "last_city_destination_iata": None,
    "last_adm4": None,           # ex: "35.73.01.1001"
    "last_city_destination_adm4": None,
    "city_turn_counter": 0,      # berapa turn sejak kota terakhir disebut

    # Flight
    "last_origin": None,         # ex: "CGK" (Jakarta)
    "last_destination": None,
    "last_flight_params": None,  # dict hasil ekstrak Amadeus

    # Confirmation state
    "awaiting_confirmation": False,
    "pending_intent": None,
    "candidates": [],
    "pending_query": None, 
    "pending_params": None,

    # Turn tracking
    "total_turns": 0,
}

# some kind of api 

def get() -> dict:
    return SESSION

def tick():
    """Panggil setiap awal turn. Increment counter dan expire kalau sudah stale."""
    SESSION["total_turns"] += 1

    if SESSION["last_city_name"] is not None:
        SESSION["city_turn_counter"] += 1

        if SESSION["city_turn_counter"] > EXPIRE_AFTER_N_TURNS:
            print(f"[Session] Konteks kota '{SESSION['last_city_name']}' expired setelah {EXPIRE_AFTER_N_TURNS} turn.")
            _reset_city()

def update_city(cityname: dict | str, adm4: str = None, iata: dict = None):
    """update city context. and incremet counter """
    if isinstance(cityname, str):
        current_origin = cityname
        current_dest = None
    else:
        # Jika dictionary, ambil pakai .get()
        current_origin = cityname.get('origin')
        current_dest = cityname.get('destination')
        
    old = SESSION["last_city_name"]
    SESSION["last_city_name"] = current_origin
    SESSION["last_city_destination_name"] = current_dest
    SESSION["last_adm4"] = adm4
    # SESSION["last_city_iata"] = iata.get('origin_iatas')
    # SESSION["last_destination"] = iata.get('destination_iatas')
    if iata and isinstance(iata, dict):
        SESSION["last_city_iata"] = iata.get('origin_iatas')
        SESSION["last_destination"] = iata.get('destination_iatas')
    else:
        SESSION["last_city_iata"] = None
        SESSION["last_destination"] = None
    SESSION["city_turn_counter"] = 0  # reset karena baru disebut
    
    if old and current_origin and old.lower() != current_origin.lower():
        print(f"[Session] kota berubah: {old} -> {current_origin}")
    else:
        print(f"[Session] Kota tersimpan: {current_origin}")
    
    # if old and old.lower() != cityname.lower():
    #     print(f"[Session] kota berubah menjadi: {old} -> {cityname}")
    # else:
    #     print(f"[Session] Kota tersimpan: {cityname}")

def update_flight(params: dict):
    SESSION["last_flight_params"] = params
    if params.get("origin"):
        SESSION["last_origin"] = params["origin"]
        
def set_confirmation(intent: str, candidates: list):
    SESSION["awaiting_confirmation"] = True
    SESSION["pending_intent"] = intent
    SESSION["candidates"] = candidates
    
def clear_confirmation():
    SESSION["awaiting_confirmation"] = False
    SESSION["pending_intent"] = None
    SESSION["candidates"] = []
    
def smart_reset_if_needed(action: str, query: str) -> bool:
    """
    Reset SESSION kalau topik benar-benar non-travel.
    Return True kalau direset.
    """
    if action != "LLM":
        return False

    q = query.lower()
    if any(topic in q for topic in NON_TRAVEL_TOPICS):
        print(f"[Session] Topik non-travel terdeteksi → reset session.")
        _reset_all()
        return True

    return False
    
def touch_city():
    """Panggil kalau kota disebut lagi tanpa perlu update nilainya."""
    SESSION["city_turn_counter"] = 0

def has_city() -> bool:
    return SESSION["last_city_name"] is not None

def has_origin() -> bool:
    return SESSION["last_origin"] is not None
    
def summary() -> str:
    """Debug print state SESSION."""
    return (
        f"city={SESSION['last_city_name']} "
        f"last city destination name ={SESSION['last_city_destination_name']} "
        f"(turn_counter={SESSION['city_turn_counter']}) | "
        f"adm4={SESSION['last_adm4']} | "
        f"last_city_destination_adm4={SESSION['last_city_destination_adm4']} | "
        f"iata={SESSION['last_city_iata']} | "
        f"origin={SESSION['last_origin']} | "
        f"last_destination={SESSION['last_destination']} |"
        f"awaiting={SESSION['awaiting_confirmation']} | "
        f"last_destination={SESSION['last_destination']}"
    )
    
# important function
def _reset_city():
    SESSION["last_city_name"] = None
    SESSION["last_city_iata"] = None
    SESSION["last_adm4"] = None
    SESSION["city_turn_counter"] = 0

def _reset_all():
    _reset_city()
    SESSION["last_origin"] = None
    SESSION["last_flight_params"] = None
    SESSION["awaiting_confirmation"] = False
    SESSION["pending_intent"] = None
    SESSION["candidates"] = []

