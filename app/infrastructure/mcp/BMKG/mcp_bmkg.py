import requests 

BMKG_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

class BMKGClient:
    def __init__(self):
        self.base_url = BMKG_URL
        self.timeout = 10

    def get_bmkg_weather(self, adm4_code: str):
        """
        Fetch prakiraan cuaca BMKG berdasarkan kode wilayah adm4
        Contoh: 31.71.03.1001 (Kelurahan Kemayoran)
        """

        params = {"adm4": adm4_code}
        print('param: ', params)

        try:
            r = requests.get(self.base_url, params=params, timeout=self.timeout)

            if r.status_code != 200:
                return {
                    "error": f"HTTP {r.status_code}",
                    "source": "BMKG"
                }

            data = r.json()

            if not data.get("data"):
                return {
                    "error": "Empty BMKG data",
                    "source": "BMKG"
                }

            forecasts = data["data"][0].get("cuaca")

            if not forecasts:
                return {
                    "error": "No forecast data",
                    "source": "BMKG"
                }

            current = forecasts[0][0]

            return {
                "source": "BMKG",
                "location_code": adm4_code,
                "analysis_date": current.get("analysis_date"),
                "local_datetime": current.get("local_datetime"),
                "temperature_c": current.get("t"),
                "humidity_percent": current.get("hu"),
                "weather": current.get("weather_desc"),
                "wind_speed_kmh": current.get("ws"),
                "visibility": current.get("vs_text")
            }

        except Exception as e:
            return {
                "error": str(e),
                "source": "BMKG"
            }
