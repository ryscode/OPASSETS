import requests, json, os
from datetime import datetime

SETS = {
    "OP01": 3188,
    "OP02": 3225,
    "OP03": 3284,
    "OP04": 3351,
    "OP05": 3395,
}

def download_prices(set_code, group_id):
    url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/prices"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            prices = response.json()
            path = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), f"prices_{set_code.lower()}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(prices, f, indent=2, ensure_ascii=False)
            print(f"✅ {set_code} gespeichert: {path}")
        else:
            print(f"❌ HTTP Error {response.status_code} für {set_code}")
    except Exception as e:
        print(f"❌ Fehler beim Verarbeiten von {set_code}: {e}")

def main():
    print(f"🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC")
    for code, group_id in SETS.items():
        download_prices(code, group_id)

if __name__ == "__main__":
    main()
