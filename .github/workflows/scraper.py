import json
import requests
from pathlib import Path

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


def build_price_data(set_code, group_id):
    products_url = BASE_PRODUCTS_URL.format(group_id=group_id)
    prices_url = BASE_PRICES_URL.format(group_id=group_id)

    products = fetch_json(products_url)
    prices = fetch_json(prices_url)

    price_lookup = {str(p["productId"]): p for p in prices.get("results", [])}

    combined = {}

    for prod in products.get("results", []):
        prod_id = str(prod.get("productId"))

        # Karten-spezifische Infos aus extendedData holen
        ext_map = {e["name"]: e["value"] for e in prod.get("extendedData", [])}

        number = ext_map.get("Number")
        if not number:
            continue

        subtype = prod.get("subTypeName")
        card_id = number
        if subtype and subtype.lower() != "normal":
            card_id += f"_{subtype.replace(' ', '').lower()}"

        norm_id = normalize_id(f"{set_code}-{card_id}")
        price_data = price_lookup.get(prod_id, {})

        combined[norm_id] = {
            "lowPrice": price_data.get("lowPrice"),
            "midPrice": price_data.get("midPrice"),
            "highPrice": price_data.get("highPrice"),
            "marketPrice": price_data.get("marketPrice"),
            "directLowPrice": price_data.get("directLowPrice"),
            "name": prod.get("name"),
            "rarity": prod.get("rarity"),
            "category": prod.get("subTypeName"),
            "cost": prod.get("convertedCost"),
            "power": prod.get("power"),
            "colors": ext_map.get("Color"),
            "attributes": ext_map.get("Attribute"),
            "types": ext_map.get("Types"),
            "effect": ext_map.get("Effect"),
            "trigger": ext_map.get("Trigger"),
            "counter": ext_map.get("Counter"),
            "imageUrl": prod.get("imageUrl"),
            "groupId": group_id
        }

    return combined


def main():
    print("🔁 Starte Scrape")
    sets = fetch_json(SET_GROUPS_URL)
    output_dir = Path("prices")
    output_dir.mkdir(exist_ok=True)

    for set_code, group_id in sets.items():
        print(f"➡️  Verarbeite {set_code} ({group_id})")
        try:
            data = build_price_data(set_code, group_id)
            output_path = output_dir / f"prices_{set_code.lower()}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ {len(data)} Preise gespeichert unter {output_path}")
        except Exception as e:
            print(f"❌ Fehler bei {set_code}: {e}")

    print("✅ Fertig!")


if __name__ == "__main__":
    main()
