import json
import os
import requests
from requests.adapters import HTTPAdapter, Retry

# 1. Set-Liste (Mapping Set-Code -> Group-ID) einlesen
try:
    with open("set_groups.json", "r") as f:
        set_groups = json.load(f)
except Exception as e:
    print(f"Fehler: konnte 'set_groups.json' nicht laden ({e})")
    set_groups = {}

# Verzeichnis für Preisdateien anlegen, falls nicht vorhanden
output_dir = "prices"
os.makedirs(output_dir, exist_ok=True)

# Sinnvollen User-Agent definieren, um als legitimer Client zu erscheinen
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/110.0.5481.178 Safari/537.36"
}

# Requests-Session einrichten mit Retry-Logik für Robustheit
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def normalize_id(raw_id):
    base = raw_id.replace("_", " ")
    parts = base.split("-")
    return f"{parts[0]}-{base}"

for set_code, group_id in set_groups.items():
    prod_url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/products"
    price_url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/prices"
    print(f"Verarbeite Set {set_code} (Gruppe {group_id})...")
    try:
        prod_resp = session.get(prod_url, headers=headers, timeout=10)
        prod_resp.raise_for_status()
        price_resp = session.get(price_url, headers=headers, timeout=10)
        price_resp.raise_for_status()
    except Exception as e:
        print(f" -> Fehler beim Abruf von Gruppe {group_id}: {e}")
        continue

    try:
        products_data = prod_resp.json().get("results", [])
    except Exception as e:
        print(f" -> Ungültige JSON-Antwort für Produkte {set_code}: {e}")
        continue
    try:
        prices_data = price_resp.json().get("results", [])
    except Exception as e:
        print(f" -> Ungültige JSON-Antwort für Preise {set_code}: {e}")
        continue

    price_lookup = {str(p["productId"]): p for p in prices_data}
    final_prices = {}

    for prod in products_data:
        prod_id = str(prod.get("productId"))
        number = prod.get("number")
        subtype = prod.get("subTypeName", "")

        if not number:
            continue

        card_id = number
        if subtype and subtype.lower() != "normal":
            card_id += f"_{subtype.replace(' ', '').lower()}"

        norm_id = normalize_id(card_id)
        price_data = price_lookup.get(prod_id, {})

        final_prices[norm_id] = {
            "lowPrice": price_data.get("lowPrice"),
            "midPrice": price_data.get("midPrice"),
            "highPrice": price_data.get("highPrice"),
            "marketPrice": price_data.get("marketPrice"),
            "directLowPrice": price_data.get("directLowPrice"),
            "name": prod.get("name"),
            "rarity": prod.get("rarity"),
            "power": prod.get("power"),
            "cost": prod.get("convertedCost"),
            "category": prod.get("subTypeName"),
            "groupId": group_id
        }

    outfile = os.path.join(output_dir, f"prices_{set_code.lower()}.json")
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(final_prices, f, ensure_ascii=False, indent=2)
        print(f" -> Preise für {set_code} gespeichert ({len(final_prices)} Einträge).")
    except Exception as e:
        print(f" -> Fehler beim Schreiben der Datei {outfile}: {e}")
