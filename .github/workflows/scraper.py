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
    base = raw_id.replace("_", " ")
    parts = base.split("-")
    return f"{parts[0]}-{base}"


def extract_extended_fields(ext_data):
    result = {
        "colors": [],
        "attributes": [],
        "types": [],
        "effect": None,
        "trigger": None,
        "counter": None
    }
    for item in ext_data:
        name = item.get("name")
        value = item.get("value")
        if name == "Color":
            result["colors"].append(value)
        elif name == "Attribute":
            result["attributes"].append(value)
        elif name == "Type":
            result["types"].append(value)
        elif name == "Effect":
            result["effect"] = value
        elif name == "Trigger":
            result["trigger"] = value
        elif name == "Counter":
            try:
                result["counter"] = int(value)
            except:
                result["counter"] = None
    return result


def build_price_data(group_id):
    products_url = BASE_PRODUCTS_URL.format(group_id=group_id)
    prices_url = BASE_PRICES_URL.format(group_id=group_id)

    products = fetch_json(products_url)
    prices = fetch_json(prices_url)

    price_lookup = {str(p["productId"]): p for p in prices.get("results", [])}

    combined = {}

    for prod in products.get("results", []):
        prod_id = str(prod.get("productId"))
        number = prod.get("number")
        subtype = prod.get("subTypeName")

        if not number:
            continue

        card_id = number
        if subtype and subtype.lower() != "normal":
            card_id += f"_{subtype.replace(' ', '').lower()}"

        norm_id = normalize_id(card_id)
        price_data = price_lookup.get(prod_id, {})

        ext_data = extract_extended_fields(prod.get("extendedData", []))

        combined[norm_id] = {
            "name": prod.get("name"),
            "rarity": prod.get("rarity"),
            "cost": prod.get("convertedCost"),
            "power": prod.get("power"),
            "category": prod.get("subTypeName"),
            "colors": ext_data["colors"],
            "attributes": ext_data["attributes"],
            "types": ext_data["types"],
            "effect": ext_data["effect"],
            "trigger": ext_data["trigger"],
            "counter": ext_data["counter"],
            "imageUrl": prod.get("imageUrl"),
            "lowPrice": price_data.get("lowPrice"),
            "midPrice": price_data.get("midPrice"),
            "highPrice": price_data.get("highPrice"),
            "marketPrice": price_data.get("marketPrice"),
            "directLowPrice": price_data.get("directLowPrice")
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
