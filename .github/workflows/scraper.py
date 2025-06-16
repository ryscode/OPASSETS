import json
import requests
from pathlib import Path
from collections import defaultdict

SET_GROUPS_URL = "https://raw.githubusercontent.com/ryscode/OPASSETS/main/prices/set_groups.json"
BASE_PRODUCTS_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/products"
BASE_PRICES_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/prices"

def fetch_json(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def normalize_id(raw_id):
    # z. B. "OP01-001_p1" → "OP01-OP01-001 p1"
    base = raw_id.replace("_", " ")
    parts = base.split("-")
    return f"{parts[0]}-{base}"

def build_price_data(group_id):
    products_url = BASE_PRODUCTS_URL.format(group_id=group_id)
    prices_url = BASE_PRICES_URL.format(group_id=group_id)

    products = fetch_json(products_url).get("results", [])
    prices = fetch_json(prices_url).get("results", [])

    product_info_map = {}
    product_number_map = {}

    for prod in products:
        pid = str(prod.get("productId"))
        extended = {
            ext.get("displayName"): ext.get("value")
            for ext in prod.get("extendedData", [])
            if ext.get("displayName") and ext.get("value") is not None
}


        product_info_map[pid] = {
            "name": prod.get("name") or extended.get("Name"),
            "rarity": prod.get("rarity") or extended.get("Rarity"),
            "power": prod.get("power") or extended.get("Power"),
            "cost": prod.get("convertedCost") or extended.get("Cost"),
            "category": prod.get("subTypeName") or extended.get("Subtype"),
            "colors": prod.get("color") or extended.get("Color"),
            "attributes": prod.get("attribute") or extended.get("Attribute"),
            "types": prod.get("types") or extended.get("Types"),
            "effect": prod.get("effect") or extended.get("Effect"),
            "trigger": prod.get("trigger") or extended.get("Trigger"),
            "counter": prod.get("counter") or extended.get("Counter"),
            "imageUrl": prod.get("imageUrl") or extended.get("Image URL"),
        
            # Zusätzliche Felder nur in extendedData
            "frameType": extended.get("Frame Type"),
            "variant": extended.get("Variant"),
            "finish": extended.get("Finish"),
            "cardType": extended.get("Card Type"),
            "description": extended.get("Description")
        }


        number = extended.get("Number")
        if number:
            product_number_map[pid] = number

    card_variants = defaultdict(list)
    for price in prices:
        pid = str(price.get("productId"))
        number = product_number_map.get(pid)
        subtype = price.get("subTypeName") or ""
        if not number:
            continue

        base_id = number
        if subtype.lower() != "normal" and subtype:
            base_id += f"_{subtype.replace(' ', '').lower()}"

        norm_id = normalize_id(base_id)
        card_variants[norm_id].append({
            "productId": pid,
            "price": {
                "lowPrice": price.get("lowPrice"),
                "midPrice": price.get("midPrice"),
                "highPrice": price.get("highPrice"),
                "marketPrice": price.get("marketPrice"),
                "directLowPrice": price.get("directLowPrice")
            }
        })

    combined = {}
    for card_id, entries in card_variants.items():
        for entry in entries:
            pid = entry["productId"]
            info = product_info_map.get(pid, {})
            combined[card_id] = {
                **entry["price"],
                **info,
                "groupId": group_id
            }
            break

    return combined


def main():
    print("🔁 Starte Scrape")
    sets = fetch_json(SET_GROUPS_URL)
    output_dir = Path("prices")
    output_dir.mkdir(exist_ok=True)

    for set_code, group_id in sets.items():
        print(f"➞️  Verarbeite {set_code} ({group_id})")
        try:
            data = build_price_data(group_id)
            output_path = output_dir / f"prices_{set_code.lower()}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ {len(data)} Preise gespeichert unter {output_path}")
        except Exception as e:
            print(f"❌ Fehler bei {set_code}: {e}")

    print("✅ Fertig!")

if __name__ == "__main__":
    main()
