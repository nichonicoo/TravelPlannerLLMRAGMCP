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
    "context": {
        "city": {
            "name": None,
            "destination_name": None,
            "iata": None,
            "destination_iata": None,
            "adm4": None,
            "destination_adm4": None,
            "turn_counter": 0,
        },
        "flight": {
            "origin": None,
            "destination": None,
            "last_params": None,
        },
        "hotel": {
            "last_results": [],
            "turn_counter": 0,
        }
    },

    "state": {
        "awaiting_confirmation": False,
        "intent": None,
        "candidates": [],
        "field": None,
        "params": None,
        "pending_query": None,
        "pending_params": None,
    },

    "meta": {
        "total_turns": 0
    }
}

# some kind of api


def get() -> dict:
    return SESSION


def tick():
    """Panggil setiap awal turn. Increment counter dan expire kalau sudah stale."""
    SESSION["meta"]["total_turns"] += 1

    if SESSION["context"]["city"]["name"] is not None:
        SESSION["context"]["city"]["turn_counter"] += 1

        if SESSION["context"]["city"]["turn_counter"] > EXPIRE_AFTER_N_TURNS:
            print(
                f"[Session] Konteks kota '{SESSION['context']['city']['name']}' expired setelah {EXPIRE_AFTER_N_TURNS} turn.")
            _reset_city()

    if SESSION["context"]["hotel"]["last_results"]:
        SESSION["context"]["hotel"]["turn_counter"] += 1

        if SESSION["context"]["hotel"]["turn_counter"] > EXPIRE_AFTER_N_TURNS:
            print("[Session] Hotel context expired.")
            SESSION["context"]["hotel"]["last_results"] = []
            SESSION["context"]["hotel"]["turn_counter"] = 0


def update_city(cityname: dict | str, adm4: str = None, iata: dict = None):
    """update city context. and increment counter """
    if isinstance(cityname, str):
        current_origin = cityname
        current_dest = None
    else:
        # Jika dictionary, ambil pakai .get()
        current_origin = cityname.get('origin')
        current_dest = cityname.get('destination')

    old = SESSION["context"]["city"]["name"]
    SESSION["context"]["city"]["name"] = current_origin
    SESSION["context"]["city"]["destination_name"] = current_dest
    SESSION["context"]["city"]["adm4"] = adm4

    if iata and isinstance(iata, dict):
        SESSION["context"]["city"]["iata"] = iata.get('origin_iatas')
        SESSION["context"]["city"]["destination_iata"] = iata.get(
            'destination_iatas')
    else:
        SESSION["context"]["city"]["iata"] = None
        SESSION["context"]["city"]["destination_iata"] = None

    SESSION["context"]["city"]["turn_counter"] = 0  # reset karena baru disebut

    if old and current_origin and old.lower() != current_origin.lower():
        print(f"[Session] kota berubah: {old} -> {current_origin}")
    else:
        print(f"[Session] Kota tersimpan: {current_origin}")


def update_flight(params: dict):
    SESSION["context"]["flight"]["last_params"] = params
    if params.get("origin"):
        SESSION["context"]["flight"]["origin"] = params["origin"]


def update_hotels(hotels: list):
    SESSION["context"]["hotel"]["last_results"] = hotels
    SESSION["context"]["hotel"]["turn_counter"] = 0


def set_confirmation(intent, field, candidates, params):
    s = SESSION["state"]
    s["awaiting_confirmation"] = True
    s["intent"] = intent
    s["field"] = field
    s["candidates"] = candidates
    s["params"] = params


def clear_confirmation():
    s = SESSION["state"]
    s["awaiting_confirmation"] = False
    s["intent"] = None
    s["field"] = None
    s["candidates"] = []
    s["params"] = None


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
    SESSION["context"]["city"]["turn_counter"] = 0


def has_hotels() -> bool:
    return len(SESSION["context"]["hotel"]["last_results"]) > 0


def has_city() -> bool:
    return SESSION["context"]["city"]["name"] is not None


def has_origin() -> bool:
    return SESSION["context"]["flight"]["origin"] is not None


def summary() -> str:
    """Debug print state SESSION."""
    return (
        f"city={SESSION['context']['city']['name']} "
        f"destination_name={SESSION['context']['city']['destination_name']} "
        f"(turn_counter={SESSION['context']['city']['turn_counter']}) | "
        f"adm4={SESSION['context']['city']['adm4']} | "
        f"destination_adm4={SESSION['context']['city']['destination_adm4']} | "
        f"iata={SESSION['context']['city']['iata']} | "
        f"origin={SESSION['context']['flight']['origin']} | "
        f"destination={SESSION['context']['flight']['destination']} | "
        f"awaiting={SESSION['state']['awaiting_confirmation']} | "
        f"hotels={len(SESSION['context']['hotel']['last_results'])} "
    )

# important function


def _reset_city():
    SESSION["context"]["city"]["name"] = None
    SESSION["context"]["city"]["iata"] = None
    SESSION["context"]["city"]["adm4"] = None
    SESSION["context"]["city"]["turn_counter"] = 0


def _reset_all():
    _reset_city()
    SESSION["context"]["flight"]["origin"] = None
    SESSION["context"]["flight"]["destination"] = None
    SESSION["context"]["flight"]["last_params"] = None
    SESSION["context"]["hotel"]["last_results"] = []
    SESSION["context"]["hotel"]["turn_counter"] = 0
    SESSION["state"]["awaiting_confirmation"] = False
    SESSION["state"]["intent"] = None
    SESSION["state"]["candidates"] = []
    SESSION["state"]["field"] = None
    SESSION["state"]["params"] = None
