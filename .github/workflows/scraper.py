import requests
import json
import os
from datetime import datetime

BASE_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/products"
SET_GROUPS_PATH = "prices/set_groups.json"
OUTPUT_DIR = "prices"

def fetch_products(group_id):
    url = BASE_URL.format(group_id=group_id)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("results", [])

def extract_card_number(product):
    # Suche nach einem Feld mit "number" oder einem ähnlichen Muster
    identifiers = product.get("extendedData", [])
    for entry in identifiers:
        if entry.get("name", "").lower() == "number":
            return entry.get("value", "").strip().upper()
    return None

def build_price_dict(products):
    price_dict = {}
    for product in products:
        number = extract_card_number(product)
        if not number:
            continue

        sub_type = next((e["value"] for e in product.get("extendedData", [])
                         if e.get("name") == "Subtype Name"), "")
        price_data = product.get("prices", {})

        key = number if sub_type.lower() in ("", "normal") else f"{number} {sub_type.lower()}"

        if price_data.get("marketPrice"):
            price_dict[key] = {
                "productId": product.get("productId"),
                "lowPrice": price_data.get("lowPrice"),
                "midPrice": price_data.get("midPrice"),
                "highPrice": price_data.get("highPrice"),
                "marketPrice": price_data.get("marketPrice"),
                "directLowPrice": price_data.get("directLowPrice"),
                "subTypeName": sub_type or "Normal"
            }
    return price_dict

def main():
    print(f"🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC")

    with open(SET_GROUPS_PATH, encoding="utf-8") as f:
        sets = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for set_name, group_id in sets.items():
        print(f"\n🔄 Verarbeite {set_name} (Group-ID {group_id})")
        try:
            products = fetch_products(group_id)
            print(f"✅ {len(products)} Produkte geladen für Gruppe {group_id}")
            price_dict = build_price_dict(products)

            if not price_dict:
                print(f"⚠️ Keine Preise extrahiert für {set_name}")
            else:
                out_path = os.path.join(OUTPUT_DIR, f"prices_{set_name.lower()}.json")
                with open(out_path, "w", encoding="utf-8") as out_file:
                    json.dump(price_dict, out_file, indent=2, ensure_ascii=False)
                print(f"💾 Gespeichert: {out_path}")

        except requests.HTTPError as e:
            print(f"❌ HTTP Error bei Set {set_name}: {e}")
        except Exception as e:
            print(f"❌ Fehler bei Set {set_name}: {e}")

    print("\n✅ Fertig!")

if __name__ == "__main__":
    main()
