import serpapi

client = serpapi.Client(api_key="5240a6289a44e356a2b85801950627ae5bbfffa5dfc8ba2e01796e132309b792")
results = client.search({
  "engine": "google_flights",
  "hl": "en",
  "gl": "us",
  "departure_id": "CGK",
  "arrival_id": "MLG",
  "outbound_date": "2026-03-26",
  "currency": "IDR",
  "type": "2",
  "adults": "1"
})

print('result: ', results)