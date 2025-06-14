import csv
import json
import os
import requests
from io import StringIO

BASE_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/products"
SET_GROUPS_FILE = "set_groups.json"
OUTPUT_DIR = "prices"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_set_groups():
    try:
        with open(SET_GROUPS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Lesen von {SET_GROUPS_FILE}: {e}")
        return {}

def fetch_csv_products(group_id):
    url = BASE_URL.format(group_id=group_id)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return list(csv.DictReader(StringIO(response.text)))
    except Exception as e:
        print(f"❌ Fehler beim Abrufen von {url}: {e}")
        return []

def build_price_dict(products):
    result = {}
    for item in products:
        number = item.get("number", "").strip()
        subtype = item.get("subTypeName", "").strip()
        key = number if not subtype or subtype.lower() == "normal" else f"{number} {subtype}"

        result[key] = {
            "productId": item.get("productId"),
            "lowPrice": try_float(item.get("lowPrice")),
            "marketPrice": try_float(item.get("marketPrice")),
            "midPrice": try_float(item.get("midPrice")),
            "highPrice": try_float(item.get("highPrice")),
            "directLowPrice": try_float(item.get("directLowPrice")),
        }
    return result

def try_float(value):
    try:
        return float(value)
    except:
        return None

def main():
    set_groups = load_set_groups()
    for set_code, group_id in set_groups.items():
        print(f"🔄 Verarbeite {set_code} ({group_id})")
        products = fetch_csv_products(group_id)
        prices = build_price_dict(products)
        out_path = os.path.join(OUTPUT_DIR, f"prices_{set_code}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(prices, f, indent=2, ensure_ascii=False)
        print(f"✅ Gespeichert: {out_path}")

if __name__ == "__main__":
    main()
