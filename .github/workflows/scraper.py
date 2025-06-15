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
        product_info_map[pid] = {
            "name": prod.get("name"),
            "rarity": prod.get("rarity"),
            "power": prod.get("power"),
            "cost": prod.get("convertedCost"),
            "category": prod.get("subTypeName"),
            "colors": prod.get("color"),
            "attributes": prod.get("attribute"),
            "types": prod.get("types"),
            "effect": prod.get("effect"),
            "trigger": prod.get("trigger"),
            "counter": prod.get("counter"),
            "imageUrl": prod.get("imageUrl")
        }

        # ➤ Hole Kartennummer aus extendedData
        number = None
        for ext in prod.get("extendedData", []):
            if ext.get("name") == "Number":
                number = ext.get("value")
                break
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
