import requests
import json
from datetime import datetime
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)"}

def download_prices(set_code, group_id):
    url = f"https://tcgcsv.com/tcgplayer/68/{group_id}/prices"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            prices = response.json()
            filename = f"prices_{set_code.lower()}.json"
            output_dir = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), "prices")
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(prices, f, indent=2, ensure_ascii=False)
            print(f"✅ {set_code} gespeichert: {path}")
        except Exception as e:
            print(f"❌ JSON Parse Error bei {set_code}: {e}")
    else:
        print(f"❌ HTTP Error {response.status_code} für {set_code}")

def main():
    print(f"🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC")

    json_path = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), "set_groups.json")
    with open(json_path, encoding="utf-8") as f:
        sets = json.load(f)

    for code, group_id in sets.items():
        download_prices(code, group_id)

if __name__ == "__main__":
    main()
