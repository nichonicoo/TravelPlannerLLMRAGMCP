from difflib import get_close_matches
import pandas as pd
import re
import os

from app.core.settings import settings


class WeatherLocationResolver:
    def __init__(self):
        self.path = os.path.join(
            settings.PROJECT_ROOT,
            "data",
            "kode-wilayah.csv"
        )

        self.df = pd.read_csv(self.path)

        self._build_index()

    def _build_index(self):
        # 1. Quantify administrative levels based on dots
        self.df["dot_count"] = (
            self.df["kode"]
            .astype(str)
            .str.count(r"\.")
        )

        # 2. Extract Cities/Regencies (ADM2 has exactly 1 dot, e.g., '32.73')
        city_df = self.df[self.df["dot_count"] == 1].copy()
        
        city_df["nama_lower"] = (
            city_df["nama"]
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace(r"^kota\s+", "", regex=True)
            .str.replace(r"^kabupaten\s+", "", regex=True)
            .str.strip()
        )

        # Remove duplicate clean city names to avoid index clashing
        city_df = city_df.drop_duplicates(subset=["nama_lower"])

        # 3. Separate Villages/Kelurahan (ADM4 has exactly 3 dots, e.g., '32.73.01.1001')
        village_df = self.df[self.df["dot_count"] == 3].copy()

        # ==================================================
        # MAP ADM2 CITIES TO A VALID ADM4 CHILD
        # ==================================================
        self.CITY_NAME_INDEX = {}

        for _, row in city_df.iterrows():
            city_code = row["kode"]          # e.g., "32.73"
            city_name = row["nama_lower"]     # e.g., "bandung"

            # Find all villages belonging to this city prefix
            # e.g., looking for villages starting with "32.73."
            child_villages = village_df[
                village_df["kode"].str.startswith(f"{city_code}.")
            ]

            if not child_villages.empty:
                # Select the first available village/kelurahan as the default weather station
                fallback_adm4 = child_villages.iloc[0]["kode"]
                self.CITY_NAME_INDEX[city_name] = fallback_adm4
            else:
                # Edge case fallback: If your dataset lacks a child record for this city, 
                # pad it manually so the API structural pattern holds up
                self.CITY_NAME_INDEX[city_name] = f"{city_code}.01.1001"

        self.ALL_CITY_NAMES = list(self.CITY_NAME_INDEX.keys())

        # ==========================================
        # COMMON USER ALIASES / TYPO FIXES
        # ==========================================
        self.ALIASES = {
            "bdg": "bandung",
            "bndg": "bandung",
            "jkt": "jakarta",
            "jogja": "yogyakarta",
            "ygy": "yogyakarta",
            "sby": "surabaya",
            "smg": "semarang",
            "dps": "denpasar",
        }

    # ==================================================
    # CLEAN USER QUERY
    # ==================================================
    def extract_location(self, text: str) -> str:

        text = text.lower()

        # remove symbols
        text = re.sub(r"[^a-z\s]", " ", text)

        words = text.split()

        stopwords = {
            "bagaimana",
            "cuaca",
            "di",
            "ke",
            "kota",
            "kabupaten",
            "hari",
            "ini",
            "gimana",
            "sekarang",
            "itu",
            "ada",
            "apa",
            "ya",
            "apakah",
            "kah",
            "yang",
            "untuk",
            "besok",
            "lusa",
            "hariini",
            "hujan",
        }

        filtered = [
            w for w in words
            if w not in stopwords
        ]

        return " ".join(filtered).strip()

    # ==================================================
    # MAIN LOCATION RESOLVER
    # ==================================================
    def getLocation(self, query, force: bool = False):

        if isinstance(query, list):
            query = query[0] if query else ""

        if not isinstance(query, str):
            return {"status": "NOT_FOUND"}

        query = query.strip().lower()

        # ------------------------------------------
        # EXTRACT LOCATION
        # ------------------------------------------
        location = (
            query
            if force
            else self.extract_location(query)
        )

        print(
            f"[LocationResolver] extracted: "
            f"'{location}' (force={force})"
        )

        if not location:
            return {"status": "NOT_FOUND"}

        # ------------------------------------------
        # APPLY ALIASES
        # ------------------------------------------
        location = self.ALIASES.get(location, location)

        print(f"[LocationResolver] normalized: '{location}'")

        # ==========================================
        # 1. EXACT MATCH
        # ==========================================
        if location in self.CITY_NAME_INDEX:
            return {
                "status": "FOUND",
                "adm4": self.CITY_NAME_INDEX[location],
                "location_name": location.title(),
            }

        # ==========================================
        # 2. TOKEN MATCH
        # ==========================================
        #
        # safer than:
        # if location in name
        #
        token_matches = [
            name
            for name in self.ALL_CITY_NAMES
            if location in name.split()
        ]

        if len(token_matches) == 1:
            match = token_matches[0]

            return {
                "status": "FOUND",
                "adm4": self.CITY_NAME_INDEX[match],
                "location_name": match.title(),
            }

        # ==========================================
        # 3. PREFIX MATCH
        # ==========================================
        startswith_matches = [
            name
            for name in self.ALL_CITY_NAMES
            if name.startswith(location)
        ]

        if len(startswith_matches) == 1:
            match = startswith_matches[0]

            return {
                "status": "FOUND",
                "adm4": self.CITY_NAME_INDEX[match],
                "location_name": match.title(),
            }

        # ==========================================
        # 4. FUZZY MATCH
        # ==========================================
        #
        # limit to short names only
        # prevents:
        # "padang bandung"
        #
        short_names = [
            name
            for name in self.ALL_CITY_NAMES
            if len(name.split()) <= 2
        ]

        matches = get_close_matches(
            location,
            short_names,
            n=1,
            cutoff=0.75
        )

        print("[LocationResolver] fuzzy matches:", matches)

        if matches:
            match = matches[0]

            return {
                "status": "FOUND",
                "adm4": self.CITY_NAME_INDEX[match],
                "location_name": match.title(),
            }

        # ==========================================
        # 5. MULTIPLE POSSIBLE MATCHES
        # ==========================================
        if len(token_matches) > 1:
            return {
                "status": "AMBIGUOUS",
                "candidates": token_matches[:5]
            }

        return {"status": "NOT_FOUND"}
