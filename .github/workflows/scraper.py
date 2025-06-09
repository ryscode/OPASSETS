import json
from datetime import date

# Beispiel-Daten
prices = {
    "OP01-001": {
        "price_jpy": 250,
        "last_updated": str(date.today())
    }
}

# Datei schreiben
with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)
