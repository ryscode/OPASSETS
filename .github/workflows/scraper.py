import requests
import csv
import json
import os
from io import StringIO
from datetime import datetime

# Aus set_groups.json die aktuelle Zuordnung Set-Name zu Group-ID
with open("prices/set_groups.json", encoding="utf-8") as f:
    SET_GROUPS = json.load(f)

BASE_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/products"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)"}


def fetch_csv_products(group_id: str):
    url = BASE_URL.format(group_id=group_id)
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        if not response.text.strip():
            print(f"⚠️ Leere Antwort von: {url}")
            return []
        csv_data = list(csv.DictReader(StringIO(response.text)))
        print(f"✅ {len(csv_data)} Produkte geladen für Gruppe {group_id}")
        return csv_data
    except Exception as e:
        print(f"❌ Fehler beim Abruf von {url}: {e}")
        return []


def build_price_dict(products: dict) -> dict:
    result = {}
    for _, item in products.items():  # <-- Fix: Verwende .items() statt einfach zu iterieren
        number = item.get("number")
        if not number:
            continue

        subtype = item.get("subTypeName", "").strip()
        if subtype.lower() != "normal":
            number += f" p{subtype}"

        key = number.strip()
        result[key] = {
            "lowPrice": item.get("lowPrice"),
            "marketPrice": item.get("marketPrice"),
            "midPrice": item.get("midPrice"),
            "highPrice": item.get("highPrice")
        }
    return result


def try_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def save_json(filename, data):
    os.makedirs("prices", exist_ok=True)
    path = f"prices/{filename}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Gespeichert: {path}")


def main():
    print(f"\n🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC\n")
    for set_code, group_id in SET_GROUPS.items():
        print(f"🔄 Verarbeite {set_code} (Group-ID {group_id})")
        products = fetch_csv_products(group_id)
        if not products:
            print(f"⚠️ Keine Produkte gefunden für {set_code}")
            continue

        prices = build_price_dict(products)
        save_json(f"prices_{set_code.lower()}.json", prices)
    print("\n✅ Fertig!\n")


if __name__ == "__main__":
    main()
