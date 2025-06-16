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

    product_groups = defaultdict(list)
    for prod in products:
        pid = str(prod.get("productId"))
        product_groups[pid].append(prod)

    # Debug: Mehrfacheinträge anzeigen
    for pid, variants in product_groups.items():
        if len(variants) > 1:
            print(f"\U0001f440 Mehrfacheintrag für productId: {pid} ({len(variants)} Varianten)")
            for i, v in enumerate(variants):
                edata = v.get("extendedData")
                print(f"  Variante {i+1}: extendedData {'leer' if not edata else 'OK'}, name: {v.get('name')}")

    # Nur erste Variante mit gültiger extendedData übernehmen
    products_deduped = []
    seen = set()
    for pid, variants in product_groups.items():
        for prod in variants:
            edata = prod.get("extendedData")
            if edata and pid not in seen:
                products_deduped.append(prod)
                seen.add(pid)
                break

    # Produktinfos extrahieren
    for prod in products_deduped:
        pid = str(prod.get("productId"))
        extended = {
            ext.get("displayName", "").strip(): ext.get("value")
            for ext in prod.get("extendedData", [])
            if ext.get("displayName") and ext.get("value") is not None
        }

        desc = extended.get("Description", "")

        product_info_map[pid] = {
            "name": prod.get("name"),
            "rarity": extended.get("Rarity"),
            "power": str(extended.get("Power")) if extended.get("Power") is not None else None,
            "cost": str(extended.get("Cost")) if extended.get("Cost") is not None else None,
            "life": str(extended.get("Life")) if extended.get("Life") is not None else None,
            "category": extended.get("Card Type"),
            "colors": extended.get("Color"),
            "attributes": extended.get("Attribute"),
            "types": extended.get("Subtype(s)"),
            "effect": "yes" if any(t in desc for t in ["[Activate:", "[On Play]", "[When Attacking]"]) else None,
            "trigger": "yes" if "[Trigger]" in desc else None,
            "counter": str(
                extended.get("Counter") or extended.get("Counter+")) if (extended.get("Counter") or extended.get("Counter+")) is not None else None,
            "imageUrl": prod.get("imageUrl"),
            "frameType": extended.get("Frame Type"),
            "variant": extended.get("Variant"),
            "finish": extended.get("Finish"),
            "cardType": extended.get("Card Type"),
            "description": desc
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

            if card_id in combined:
                unique_id = f"{card_id}__{pid}"
            else:
                unique_id = card_id

            combined[unique_id] = {
                **entry["price"],
                **info,
                "groupId": group_id
            }

    return combined

def main():
    print("\U0001f501 Starte Scrape")
    sets = fetch_json(SET_GROUPS_URL)
    output_dir = Path("prices")
    output_dir.mkdir(exist_ok=True)

    for set_code, group_id in sets.items():
        print(f"\u279e\ufe0f  Verarbeite {set_code} ({group_id})")
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
