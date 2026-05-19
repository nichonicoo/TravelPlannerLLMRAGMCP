import os
import pandas as pd
from difflib import get_close_matches
import app.core.sessions as session
from app.core.settings import settings
from app.schemas.actions import ActionType


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

PRIORITY_AIRPORTS = {
    "jakarta": ["CGK", "HLP"],
    "bali": ["DPS"],
    "malang": ["MLG"],
    "bandung": ["BDO"]
}


class Resolver:
    def __init__(self):
        self.project_root = settings.PROJECT_ROOT
        self.carrier_index = self._build_carrier_code_index()
        self.iata_index = self._build_iata_index()
        self.iata_fullname_map = self._build_iata_to_airport_map()

    def get_carrier_name(self, code: str) -> str:
        if not code:
            return "-"

        code = code.strip().upper()

        if code in self.carrier_index:
            return self.carrier_index[code]

        if code in CARRIER_ALIASES:
            print('ini:')
            return CARRIER_ALIASES[code]

        print('code airlines: {code}')

        return code

    def get_airport_full_name(self, iata: str) -> str:
        if not iata:
            return iata

        return self.iata_fullname_map.get(iata.upper(), iata)

    def get_city_fuzzy(self, name):
        if not name:
            return None

        # Cek langsung di index
        if name in self.iata_index:
            return self.iata_index[name]

        # Kalau ga ada, coba fuzzy match
        matches = get_close_matches(
            name, self.iata_index.keys(), n=1, cutoff=0.7)
        if matches:
            matched_city = matches[0]
            print(f"Fuzzy match: '{name}' -> '{matched_city}'")
            return self.iata_index[matched_city]

        # Kalau tetap ga ada, kembalikan None sesuai maumu
        return None

    def city_to_iata(self, city_name: dict) -> dict | None:
        if not city_name:
            return None

        origin_raw = city_name.get('origin')
        dest_raw = city_name.get('destination')

        city_origin = origin_raw.lower().strip() if origin_raw else None
        city_destination = dest_raw.lower().strip() if dest_raw else None

        print('city origin:', city_origin,
              'city_destination:', city_destination)

        result = {}

        if city_origin:
            if city_origin in PRIORITY_AIRPORTS:
                result['origin_iatas'] = PRIORITY_AIRPORTS[city_origin]
            else:
                result['origin_iatas'] = self.get_city_fuzzy(city_origin)
            # IATA_INDEX.get(city_origin, []) if city_origin else None
        if city_destination:
            if city_destination in PRIORITY_AIRPORTS:
                result['destination_iatas'] = PRIORITY_AIRPORTS[city_destination]
            else:
                result['destination_iatas'] = self.get_city_fuzzy(
                    city_destination)
            # IATA_INDEX.get(city_destination, []) if city_destination else None

        print('[IATA RESULT]: ', result)
        return result

    def resolve(self, query: str) -> dict:
        s = session.get()
        state = s["state"]

        intent = state["intent"]
        candidates = state.get("candidates", [])
        params = state.get("params", {})
        field = state.get("field")

        choice = query.strip()

        selected = None

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                selected = candidates[idx]
            else:
                if choice in candidates:
                    selected = choice

        if not selected:
            return {
                "action": ActionType.INVALID_INPUT,
                "message": "Pilihan tidak valid."
            }

        # ===== WEATHER =====
        if intent == "WEATHER":
            params[field] = selected
            session.clear_confirmation()

            return {
                "action": "RETRY",
                "intent": "WEATHER",
                "params": params
            }

        # ===== FLIGHT (complex case) =====
        if intent == "FLIGHT":
            if field:
                params[field] = selected

            session.clear_confirmation()

            return {
                "action": "RETRY",
                "intent": "FLIGHT",
                "params": params
            }

        return {"status": "ERROR", "message": "Unknown confirmation state"}

    def process_result(self, intent: str, result: dict) -> str:
        if intent == "WEATHER":
            return self._handle_weather(result)

        if intent == "FLIGHT":
            return self._handle_flight(result)

        if intent == "HOTEL":
            return self._handle_hotel(result)

        return result

    def _handle_weather(self, result: dict) -> str:
        status = result.get("status")
        payload = result.get("data", {})


        if status == "OK":
            session.update_city(
                cityname=payload.get("location_name"),
                adm4=payload.get("adm4"),
            )
            session.clear_confirmation()

            return {
                "action": ActionType.GENERATE_RESPONSE,
                "data": {
                    "weather": payload.get("weather"),
                    "location_name": payload.get("location_name")
                }
            }

        if status == "AMBIGUOUS":
            candidates = payload.get("candidates", [])
            field = payload.get("field")

            session.set_confirmation(
                intent="WEATHER",
                candidates=candidates,
                field=field,
                params=payload.get("params", {})
            )

            formatted = "\n".join([
                f"{i+1}. {candidate}"
                for i, candidate in enumerate(candidates)
            ])

            return {
                "action": ActionType.ASK_CLARIFICATION,
                "message": f"Lokasi tidak dikenali secara pasti. Maksudnya yang mana?\n{formatted}"
            }

        if status == "NOT_FOUND":
            return {
                "action": ActionType.INVALID_INPUT,
                "message": "Maaf, lokasi tidak dikenali. Sebutkan nama kota yang lebih spesifik."
            }

        return {
            "action": ActionType.ERROR,
            "message": "Maaf, terjadi kesalahan saat mengambil data cuaca."
        }

    def _handle_flight(self, result: dict) -> dict:
        status = result.get("status")
        payload = result.get("data", {})

        if status == "OK":
            params = payload.get("params", {})

            session.update_flight(params)
            session.clear_confirmation()

            return {
                "action": ActionType.GENERATE_RESPONSE,
                "data": {
                    "offers": payload.get("offers", []),
                    "params": params
                }
            }

        if status == "NEED_INFO":
            missing_fields = payload.get("missing_fields", [])

            session.set_confirmation(
                intent="FLIGHT",
                candidates=[],
                field="missing",
                params=payload.get("params", {})
            )

            field_map = {
                "departure_id": "kota asal",
                "arrival_id": "kota tujuan",
                "outbound_date": "tanggal keberangkatan"
            }

            readable = [
                field_map.get(field, field)
                for field in missing_fields
            ]

            return {
                "action": ActionType.NEED_MORE_INFO,
                "message": f"Lengkapi: {', '.join(readable)}"
            }

        if status == "AMBIGUOUS":
            candidates = payload.get("candidates", [])
            field = payload.get("field")

            session.set_confirmation(
                intent="FLIGHT",
                candidates=candidates,
                field=field,
                params=payload.get("params", {})
            )

            formatted = "\n".join([
                f"{i+1}. {self.get_airport_full_name(c)}"
                for i, c in enumerate(candidates)
            ])

            return {
                "action": ActionType.ASK_CLARIFICATION,
                "message": f"Bandara tidak spesifik:\n{formatted}"
            }

        if status == "NOT_FOUND":
            return {
                "action": ActionType.INVALID_INPUT,
                "message": "Tidak ada penerbangan ditemukan."
            }

        return {
            "action": ActionType.ERROR,
            "message": "Terjadi kesalahan flight."
        }

    def _handle_hotel(self, result: dict) -> dict:
        if result.get("status") == "OK":
            session.update_hotels([
                {
                    "name": h.get("name"),
                    "token": h.get("property_token")
                }
                for h in result.get("properties", [])[:5]
            ])

            return {
                "action": ActionType.GENERATE_RESPONSE,
                "message": result.get("data")
            }

        if result.get("status") == "NEED_INFO":
            return {
                "action": ActionType.NEED_MORE_INFO,
                "message": result.get("message")
            }

        return {
            "action": ActionType.ERROR,
            "message": result.get("message", "Error hotel")
        }

    def _build_carrier_code_index(self) -> dict:
        csv_path = os.path.join(self.project_root, "data", "carriers.csv")
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

    def _build_iata_index(self) -> dict:
        csv_path = os.path.join(self.project_root, "data", "airport-codes.csv")
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
                (df["type"].isin(["large_airport", "medium_airport"])) &
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
                if isinstance(iata, str):
                    iata = [iata]  # Handle kalau cuma string
                for code in iata:
                    add_to_index(alias, code)

            # df.to_csv('output_filtered.csv')
            return index

        except Exception as e:
            print(f"[IATA Index] Gagal load CSV: {e}")
            return {}

    def _build_iata_to_airport_map(self):
        csv_path = os.path.join(self.project_root, "data", "airport-codes.csv")
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
