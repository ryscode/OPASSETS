import json
import requests
from pathlib import Path
from collections import defaultdict

def build_price_data(group_id):
    products_url = BASE_PRODUCTS_URL.format(group_id=group_id)
    prices_url = BASE_PRICES_URL.format(group_id=group_id)

    products = fetch_json(products_url).get("results", [])
    prices = fetch_json(prices_url).get("results", [])

    product_info_map = {}
    product_number_map = {}

    for prod in products:
        pid = str(prod.get("productId"))

        # Normalisiertes extendedData-Mapping über displayName
        extended = {
            ext.get("displayName", "").strip(): ext.get("value")
            for ext in prod.get("extendedData", [])
            if ext.get("displayName") and ext.get("value") is not None
        }

        desc = extended.get("Description", "")

        product_info_map[pid] = {
            "name": prod.get("name"),
            "rarity": extended.get("Rarity"),
            "power": extended.get("Power"),
            "cost": extended.get("Cost"),
            "life": extended.get("Life"),
            "category": extended.get("Card Type"),
            "colors": extended.get("Color"),
            "attributes": extended.get("Attribute"),
            "types": extended.get("Subtype(s)"),
            "effect": "yes" if any(t in desc for t in ["[Activate:", "[On Play]", "[When Attacking]"]) else None,
            "trigger": "yes" if "[Trigger]" in desc else None,
            "counter": extended.get("Counter") or extended.get("Counter+"),
            "imageUrl": prod.get("imageUrl"),

            # Weitere optionale Felder
            "frameType": extended.get("Frame Type"),
            "variant": extended.get("Variant"),
            "finish": extended.get("Finish"),
            "cardType": extended.get("Card Type"),
            "description": desc
        }

        number = extended.get("Number")
        if number:
            product_number_map[pid] = number

    # Preisdaten mit Varianten gruppieren
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
            break  # nur erste Variante verwenden

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
