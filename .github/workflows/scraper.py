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

for set_code, group_id in set_groups.items():
    # URLs für Produkte und Preise dieses Sets
    prod_url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/products"
    price_url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/prices"
    print(f"Verarbeite Set {set_code} (Gruppe {group_id})...")
    try:
        # 2. API-Abfragen für Produkte und Preise
        prod_resp = session.get(prod_url, headers=headers, timeout=10)
        prod_resp.raise_for_status()    # HTTP-Fehler auslösen, falls Statuscode != 200
        price_resp = session.get(price_url, headers=headers, timeout=10)
        price_resp.raise_for_status()
    except Exception as e:
        print(f" -> Fehler beim Abruf von Gruppe {group_id}: {e}")
        continue  # Zum nächsten Set überspringen

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

    # 3. Produkte nach Karten filtern (nur Einzelnkarten mit Nummer)
    product_map = {}
    for prod in products_data:
        # Kartennummer aus extendedData extrahieren (falls vorhanden)
        card_number = None
        for ext in prod.get("extendedData", []):
            if ext.get("name") == "Number":
                card_number = ext.get("value")
                break
        if not card_number:
            continue
        product_map[prod["productId"]] = {
            "name": prod.get("name", ""),
            "number": card_number,
            "rarity": prod.get("rarity"),
            "cost": prod.get("convertedCost"),
            "power": prod.get("power"),
            "subType": prod.get("subTypeName")
        }

    if not product_map:
        print(f" -> Keine Karten in Set {set_code} gefunden (ggf. Gruppe überspringen).")
        continue

    # 4. Preise mit Produkten zusammenführen
    prices_by_id = {}

    for price in prices_data:
        pid = price.get("productId")
        if pid not in product_map:
            continue
        info = product_map[pid]
        card_num = info["number"]
        subtype = price.get("subTypeName") or info.get("subType") or ""

        if card_num not in prices_by_id:
            prices_by_id[card_num] = []
        prices_by_id[card_num].append({
            "subType": subtype,
            "prices": {
                "lowPrice": price.get("lowPrice"),
                "midPrice": price.get("midPrice"),
                "highPrice": price.get("highPrice"),
                "marketPrice": price.get("marketPrice"),
                "directLowPrice": price.get("directLowPrice")
            }
        })

    # 5. Varianten sortieren und ID zuweisen
    final_prices = {}
    for card_num, entries in prices_by_id.items():
        entries.sort(key=lambda x: (x["subType"].lower() != "normal", str(x["subType"])) )
        base_seen = False
        variant_count = 0
        for entry in entries:
            sub = entry["subType"]
            prices_dict = entry["prices"]
            if not base_seen and sub.lower() == "normal":
                card_id = f"{set_code}-{card_num}"
                base_seen = True
            else:
                variant_count += 1
                card_id = f"{set_code}-{card_num} p{variant_count}"
            final_prices[card_id] = prices_dict

    # 6. Datei schreiben
    outfile = os.path.join(output_dir, f"prices_{set_code.lower()}.json")
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(final_prices, f, ensure_ascii=False, indent=2)
        print(f" -> Preise für {set_code} gespeichert ({len(final_prices)} Einträge).")
    except Exception as e:
        print(f" -> Fehler beim Schreiben der Datei {outfile}: {e}")
