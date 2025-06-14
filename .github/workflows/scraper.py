import requests
import json
import os
from datetime import datetime

SET_GROUPS_PATH = "prices/set_groups.json"
OUTPUT_DIR = "prices"
BASE_URL = "https://tcgcsv.com/tcgplayer/68"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)"}

def load_set_groups():
    with open(SET_GROUPS_PATH, encoding="utf-8") as f:
        return json.load(f)

def fetch_json(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def sanitize_number(number, subtype):
    if subtype and subtype.lower() != "normal":
        return f"{number} {subtype}"
    return number

def build_price_dict(products, prices):
    combined = {}
    for product in products:
        pid = str(product.get("productId"))
        price_data = prices.get(pid)
        if not price_data:
            continue

        number = product.get("cleanName") or product.get("number")
        if not number:
            continue

        subtype = product.get("subTypeName", "")
        key = sanitize_number(number, subtype)
        combined[key] = {
            "productId": pid,
            "lowPrice": price_data.get("lowPrice"),
            "marketPrice": price_data.get("marketPrice")
        }
    return combined

def save_prices(set_code, price_dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"prices_{set_code.lower()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(price_dict, f, indent=2, ensure_ascii=False)
    print(f"💾 Gespeichert: {path} ({len(price_dict)} Einträge)")

def main():
    print(f"🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC\n")
    sets = load_set_groups()

    for set_code, group_id in sets.items():
        print(f"🔄 Verarbeite {set_code} (Group-ID {group_id})")
        try:
            products = fetch_json(f"{BASE_URL}/{group_id}/products")
            print(f"✅ {len(products)} Produkte geladen für Gruppe {group_id}")

            prices = fetch_json(f"{BASE_URL}/{group_id}/prices")
            result = build_price_dict(products, prices)

            if result:
                save_prices(set_code, result)
            else:
                print(f"⚠️ Keine Preise extrahiert für {set_code}\n")
        except Exception as e:
            print(f"❌ Fehler bei Set {set_code}: {e}\n")

    print("✅ Fertig!")

if __name__ == "__main__":
    main()
