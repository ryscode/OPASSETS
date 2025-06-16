#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper With Metadata – holt Produkte + Preise von tcgcsv.com
und speichert pro Set eine JSON-Datei (prices_<set>.json).
Alle Extended-Data-Felder (Rarity, Cost, Power, …) werden mitgeschrieben.
"""

import json
import re
import requests
from pathlib import Path
from collections import defaultdict

# --------------------------------------------------------------------------- #
# Konfiguration
# --------------------------------------------------------------------------- #
SET_GROUPS_URL   = "https://raw.githubusercontent.com/ryscode/OPASSETS/main/prices/set_groups.json"
BASE_PRODUCTS_URL = "https://tcgcsv.com/tcgplayer/68/{group_id}/products"
BASE_PRICES_URL   = "https://tcgcsv.com/tcgplayer/68/{group_id}/prices"
OUT_DIR           = Path("prices")
OUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def fetch_json(url: str) -> dict:
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def normalize_id(raw_id: str) -> str:
    """
    "OP01-001_p1" → "OP01-OP01-001 p1"
    """
    base  = raw_id.replace("_", " ")
    parts = base.split("-")
    return f"{parts[0]}-{base}"

def extract_extended_data(prod: dict) -> dict:
    """legt alle extendedData-Einträge in ein dict (lower-cased keys)"""
    ext = {}
    for item in prod.get("extendedData", []):
        k, v = item.get("name"), item.get("value")
        if k and v:
            ext[k.lower()] = v
    return ext

# --------------------------------------------------------------------------- #
# Kernlogik
# --------------------------------------------------------------------------- #
def build_price_data(group_id: int) -> dict:
    products = fetch_json(BASE_PRODUCTS_URL.format(group_id=group_id)).get("results", [])
    prices   = fetch_json(BASE_PRICES_URL.format(group_id=group_id)).get("results", [])

    product_info_map   = {}
    product_number_map = {}   # productId → "OP01-001" usw.

    # 1) Produkt-Metadaten + Kartennummern sammeln
    for prod in products:
        pid       = str(prod.get("productId"))
        ext_data  = extract_extended_data(prod)

        product_info_map[pid] = {             # Metadaten (alles optional)
            "name"      : prod.get("name"),
            "rarity"    : prod.get("rarity")        or ext_data.get("rarity"),
            "power"     : prod.get("power")         or ext_data.get("power"),
            "cost"      : prod.get("convertedcost") or ext_data.get("cost"),
            "category"  : prod.get("subTypeName"),
            "colors"    : prod.get("color"),
            "attributes": prod.get("attribute"),
            "types"     : prod.get("types"),
            "effect"    : prod.get("effect"),
            "trigger"   : prod.get("trigger"),
            "counter"   : prod.get("counter"),
            "imageUrl"  : prod.get("imageUrl")
        }

        # ---- Kartennummer bestimmen -------------------------------------- #
        number = ext_data.get("number")

        # ⛑️  Fallback: Nummer aus dem Produktnamen in eckigen Klammern
        if not number:
            m = re.search(r"\[(OP\d{2}-\d{3})]", prod.get("name", ""))
            if m:
                number = m.group(1)

        if number:
            product_number_map[pid] = number
        else:
            print(f"⚠️  Kein 'Number' für PID {pid}: {prod.get('name')!r}")

    # 2) Preise pro Karten-ID zusammenführen
    card_variants = defaultdict(list)  # normalizedId → [ {productId, price{…}} … ]

    for price in prices:
        pid       = str(price.get("productId"))
        number    = product_number_map.get(pid)
        subtype   = (price.get("subTypeName") or "").strip()

        if not number:
            # Booster-Boxen, DON!!-Karten etc. – nicht relevant
            continue

        base_id = number
        if subtype and subtype.lower() != "normal":
            # "Parallel", "Alternate Art Foil" …
            base_id += f"_{subtype.replace(' ', '').lower()}"

        norm_id = normalize_id(base_id)
        card_variants[norm_id].append({
            "productId": pid,
            "price": {
                "lowPrice"      : price.get("lowPrice"),
                "midPrice"      : price.get("midPrice"),
                "highPrice"     : price.get("highPrice"),
                "marketPrice"   : price.get("marketPrice"),
                "directLowPrice": price.get("directLowPrice")
            }
        })

    # 3) Erstes Produkt-Match enthält Metadaten – danach JSON zusammenbauen
    combined = {}
    for card_id, entries in card_variants.items():
        # nimm das erste Preis-Entry (beliebig – meist identische Preise)
        entry = entries[0]
        pid   = entry["productId"]
        combined[card_id] = {
            **entry["price"],
            **product_info_map.get(pid, {}),
            "groupId": group_id
        }

    return combined

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    print("🔁  Starte Scrape")
    sets = fetch_json(SET_GROUPS_URL)          # {"OP01": 3188, …}

    for set_code, group_id in sets.items():
        print(f"➞  Verarbeite {set_code} (Group {group_id})")
        try:
            data = build_price_data(group_id)
            out  = OUT_DIR / f"prices_{set_code.lower()}.json"
            with out.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅  {len(data):>4} Einträge gespeichert → {out}")
        except Exception as e:
            print(f"❌  Fehler bei {set_code}: {e}")

    print("🏁  Fertig!")

if __name__ == "__main__":
    main()
