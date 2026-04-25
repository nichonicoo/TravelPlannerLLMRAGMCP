from difflib import get_close_matches
import pandas as pd
import re
import os
from app.core.settings import settings


class WeatherLocationResolver:
    def __init__(self):
        self.path = os.path.join(
            settings.PROJECT_ROOT, 'data', 'kode-wilayah.csv')
        self.df = pd.read_csv(self.path)
        self._build_index()

    def _build_index(self):
        # ADM4 = kode yang punya 3 titik (contoh: 11.01.01.2001)
        self.df["dot_count"] = self.df["kode"].astype(str).str.count(r"\.")
        self.ADM4_DF = self.df[self.df["dot_count"] == 3].copy()

        # bikin kolom lowercase untuk matching
        self.ADM4_DF["nama_lower"] = self.ADM4_DF["nama"].str.lower()

        # index dictionary biar cepat
        self.ADM4_NAME_INDEX = {
            row["nama_lower"]: row["kode"]
            for _, row in self.ADM4_DF.iterrows()
        }

        # print(self.ADM4_NAME_INDEX)

# ADM4_LOOKUP = {
#     "yogyakarta": "34.71.01.1001",
#     "jogja": "34.71.01.1001",
#     "yogya": "34.71.01.1001",
#     "bandung": "32.73.01.1001",
#     "kemayoran": "31.71.03.1001",
# }


    def extract_location(self, text: str) -> str:
        text = text.lower()

        text = re.sub(r"[^a-z\s]", "", text)

        words = text.split()

        stopwords = [
            "bagaimana", "cuaca", "di", "ke", "kota",
            "hari", "ini", "gimana", "sekarang", "itu", "ada", "apa", "ya"
        ]

        filtered = [w for w in words if w not in stopwords]

        # for w in stopwords:
        #     text = text.replace(w, "")

        return " ".join(filtered).strip()


    def normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z\s]", "", text)
        text = text.replace("kota", "")
        return text.strip()


    def getLocation(self, query: str, force: bool = False) -> dict:
        # print('query: ', query)
        if isinstance(query, list):
            query = query[0] if query else ""

        if not isinstance(query, str):
            return {"status": "NOT_FOUND"}

        q = query.lower().strip()

        # locations = extract_location(query)
        locations = query.lower().strip() if force else self.extract_location(query)
        print(f"[LocationResolver] extracted: '{locations}' (force={force})")

        print('loc: ', locations)

        if locations in self.ADM4_NAME_INDEX:
            return {
                "status": "FOUND",
                "adm4": self.ADM4_NAME_INDEX[locations],
                "location_name": locations.title(),
            }

        # for partial match
        candidates = [
            name for name in self.ADM4_NAME_INDEX
            if locations in name
        ]

        if len(candidates) == 1:
            return {
                'status': "FOUND",
                'adm4': self.ADM4_NAME_INDEX[candidates[0]],
                "location_name": candidates[0].title()
            }

        matches = get_close_matches(
            locations, self.ADM4_NAME_INDEX.keys(), n=1, cutoff=0.6)

        print('matches: ', matches)

        if matches:
            return {
                "status": "FOUND",
                "adm4": self.ADM4_NAME_INDEX[matches[0]],
                "location_name": matches[0].title()
            }

        if len(candidates) > 1:
            return {
                "status": "AMBIGUOUS",
                "candidates": candidates
            }
        return {"status": "NOT_FOUND"}

# def get_adm4_candidates(user_text: str):

#     location = extract_location(user_text)

#     print('extract', location)

#     if not location:
#         return {"status": "NOT_FOUND"}

#     norm =  normalize(location)

#     # 1. exact
#     if norm in ADM4_LOOKUP:
#         return {
#             "status": "FOUND",
#             "adm4": ADM4_LOOKUP[norm],
#             "name": norm
#         }

#     candidates = get_close_matches(
#         norm,
#         ADM4_LOOKUP.keys(),
#         n = 3,
#         cutoff= 0.6
#     )

#     if candidates:
#         return {
#             "status": "AMBIGUOUS",
#             "candidates": candidates
#         }

#     return {
#         "status": "NOT_FOUND"
#     }
