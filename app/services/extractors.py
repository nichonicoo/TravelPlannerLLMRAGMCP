"""
Utility functions for extracting information from user queries.
These functions use LLM to parse and understand user intent.
"""

import json
import re
from datetime import date, timedelta
from app.infrastructure.llm.base import LLMProvider


class Extractor:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def extract_city(self, query: str) -> dict | None:
        """
        Extract city names (origin and/or destination) from a user query.

        Args:
            query: User's natural language query
            llm: LLM provider instance

        Returns:
            Dictionary with 'origin' and 'destination' keys, or None if no cities found
            Example: {"origin": "Jakarta", "destination": "Bali"}
        """
        prompt = f"""Ekstrak nama kota (origin) atau lokasi wisata (destination) dari kalimat berikut.
                Balas HANYA JSON: {{"origin": "nama", "destination": "nama"}}
                Jika tidak ada, balis: None

                Contoh:
                - "ada apa di malang?" → {{"origin": None, "destination": "Malang"}}
                - "cuaca hari ini?" → {{"origin": None, "destination": None}}
                - "tiket ke bali" → {{"origin": None, "destination": "Bali"}}
                - "Berapa harga tiket dari jakarta ke bali ?" → {{"origin": "Jakarta", "destination": "Bali"}}
                - "tiket ke bali dari jakarta" → {{"origin": "Jakarta", "destination": "Bali"}}
                - "terbang ke malang" → {{"origin": null, "destination": "Malang"}}

                Kalimat: "{query}"
                """
        answer = self.llm.generate(prompt)

        if not answer or "NONE" in answer.upper():
            return None

        try:
            return json.loads(answer)
        except Exception as e:
            print(f"[LLM Error] Gagal parse JSON: {e}")
            return None

    def reference_prev_locations(self, query: str) -> bool:
        """
        Check if the query references previously mentioned locations
        using pronouns or context references like "di situ", "ke sana", etc.

        Args:
            query: User's natural language query
            llm: LLM provider instance

        Returns:
            True if query references previous locations, False otherwise
        """
        prompt = f"""Apakah kalimat ini menggunakan kata ganti seperti
                    "di situ", "ke sana", "di sana", "ke situ", "di tempat itu",
                    atau merujuk ke lokasi yang sudah disebutkan sebelumnya?

                    Jawab HANYA: YA atau TIDAK.

                    Kalimat: "{query}"
                    """
        answer = self.llm.generate(prompt)
        if not answer:
            return False

        return answer.strip().upper().startswith("YA")

    def build_flight_params(self, query: str, session_data: dict) -> dict:
        """Extract flight parameters using LLM."""
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        # Build session context
        session_context = ""
        if session_data["context"]["city"]["name"]:
            session_context += f"\n- Kota asal sebelumnya: {session_data['context']['city']['name']}"
        if session_data["context"]["city"]["destination_name"]:
            session_context += f"\n- Kota tujuan sebelumnya: {session_data['context']['city']['destination_name']}"
        if session_data["context"]["city"]["iata"]:
            session_context += f"\n- Departure ID: {session_data['context']['city']['iata']}"
        if session_data["context"]["city"]["destination_iata"]:
            session_context += f"\n- Arrival ID: {session_data['context']['city']['destination_iata']}"

        prompt = f"""Ekstrak parameter penerbangan dari query user berikut.
                            Balas HANYA dalam format JSON, tanpa penjelasan, tanpa backtick.
                            
                            Aturan:
                            - departure_id: Gunakan IATA dari Konteks jika kota sama dengan sebelumnya, jika tidak berikan null
                            - arrival_id: Gunakan IATA dari Konteks jika kota sama dengan sebelumnya, jika tidak berikan null
                            - departure_date: format YYYY-MM-DD. Jika tidak disebutkan, gunakan {tomorrow}
                            - return_date: format YYYY-MM-DD jika round trip, null jika one way
                            - type: Format angka. Jika return_date tidak disebutkan maka (2 One Way), Jika return_date ada maka (1 Round Trip)
                            - adults: jumlah penumpang, default 1
                            - children: jika ada maka tambahkan, jika tidak ada maka default null
                            - infants_in_seat: jika ada maka tambahkan, jika tidak ada maka default null
                            - infants_on_lap: jika ada maka tambahkan, jika tidak ada maka default null
                            - Jika user tidak ada batasan harga, set max_price menjadi null, jika ada maka buat dengan format angka = 970000
                            - travel_class: Jawab dengan nomor dengan urutan seperti (1 Ekonomi), (2 Premium Economy), (3 Business), (4 First)
                            - Currency ditentukan dengan bahasa apa yang diberikan oleh user. Jika user berbicara dengan bahasa indonesia maka IDR jika user berbicara dengan bahasa inggris maka USD
                            
                            Konteks sesi saat ini:{session_context if session_context else " (tidak ada)"}
                            Hari ini: {today}
                            
                            Query: "{query}"
                            
                            Contoh Format output:
                            {{
                            "departure_id": "CGK",
                            "arrival_id": "MLG",
                            "type": "2",
                            "outbound_date": "2025-08-01",
                            "return_date": null,
                            "adults": 1,
                            "children": null,
                            "max_price": null,
                            "travel_class": "1",
                            "currency": "IDR"
                            }}"""

        answer = self.llm.generate(prompt)

        if not answer:
            return {"query": query}

        try:
            clean = re.sub(r"```.*?```", "", answer, flags=re.DOTALL).strip()
            clean = re.sub(r"```", "", clean).strip()
            params = json.loads(clean)
            return params
        except json.JSONDecodeError as e:
            print(f"[ParamBuilder] JSON parse error: {e}\nRaw: {answer}")
            return {"query": query}

    def build_hotel_params(self, query: str, session_data: dict) -> dict:
        """Extract hotel parameters using LLM."""
        today = date.today()
        check_in = (today + timedelta(days=1)).isoformat()
        check_out = (today + timedelta(days=2)).isoformat()

        # Build session context
        session_context = ""
        if session_data["context"]["city"]["name"]:
            session_context += f"\n- Kota sebelumnya: {session_data['context']['city']['name']}"
        if session_data["context"]["city"]["destination_name"]:
            session_context += f"\n- Kota tujuan sebelumnya: {session_data['context']['city']['destination_name']}"

        prompt = f"""Ekstrak parameter hotel dari query user berikut.
                            Balis HANYA dalam format JSON, tanpa penjelasan, tanpa backtick.
                            
                            Aturan:
                            - location: nama kota atau lokasi. Gunakan dari Konteks jika user merujuk ke lokasi sebelumnya
                            - check_in_date: format YYYY-MM-DD. Jika tidak disebutkan, gunakan {check_in}
                            - check_out_date: format YYYY-MM-DD. Jika tidak disebutkan, gunakan {check_out}
                            - adults: jumlah tamu dewasa, default 1
                            - children: jumlah anak, default 0
                            - currency: IDR jika bahasa Indonesia, USD jika bahasa Inggris
                            - sort_by: 3 jika user minta yang murah, null jika tidak
                            - min_price: null jika tidak ada batasan
                            - max_price: angka jika user sebut batas harga, null jika tidak
                            
                            Konteks sesi saat ini:{session_context if session_context else " (tidak ada)"}
                            
                            Query: "{query}"
                            
                            Contoh Format output:
                            {{
                            "location": "Bali",
                            "check_in_date": "2025-08-01",
                            "check_out_date": "2025-08-03",
                            "adults": 2,
                            "children": 0,
                            "currency": "IDR",
                            "sort_by": null,
                            "min_price": null,
                            "max_price": null
                            }}"""

        answer = self.llm.generate(prompt)

        if not answer:
            return {"query": query}

        try:
            clean = re.sub(r"```.*?```", "", answer, flags=re.DOTALL).strip()
            clean = re.sub(r"```", "", clean).strip()
            params = json.loads(clean)
            return params
        except json.JSONDecodeError as e:
            print(f"[ParamBuilder] JSON parse error: {e}\nRaw: {answer}")
            return {"query": query}
