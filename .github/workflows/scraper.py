import requests
import pandas as pd
import json

def main():
    # Lade Kategorien
    categories_url = "https://tcgcsv.com/tcgplayer/categories.json"
    categories = requests.get(categories_url).json()

    # Finde "One Piece Card Game"
    one_piece = next((c for c in categories if "one piece" in c["name"].lower()), None)
    if not one_piece:
        print("One Piece Card Game Kategorie nicht gefunden.")
        return

    category_id = one_piece["groupId"]
    print(f"Gefundene Kategorie: {one_piece['name']} (ID: {category_id})")

    # Hole CSV-Link für aktuelle Preise
    csv_url = f"https://tcgcsv.com/tcgplayer/{category_id}/prices.csv"
    response = requests.get(csv_url)
    response.raise_for_status()

    # CSV in DataFrame laden
    df = pd.read_csv(pd.compat.StringIO(response.text))

    # Reduziere auf wichtige Spalten
    columns = ["productId", "name", "setName", "marketPrice"]
    df = df[columns].dropna(subset=["marketPrice"])

    # Preis-Mapping nach Card-ID oder Name
    price_data = {}
    for _, row in df.iterrows():
        card_id = str(row["productId"])
        price_data[card_id] = {
            "name": row["name"],
            "set": row["setName"],
            "price": round(row["marketPrice"], 2)
        }

    # Speichern in JSON-Datei
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(price_data, f, indent=2, ensure_ascii=False)

    print(f"{len(price_data)} Kartenpreise gespeichert in prices.json")

if __name__ == "__main__":
    main()

