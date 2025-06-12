import requests
import json
import os
from datetime import datetime

SETS = ["OP01", "OP02", "OP03", "OP04", "OP05"]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)"}

def download_prices(set_code):
    url = f"https://tcgcsv.com/api/onepiece/{set_code}.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            prices = response.json()
            workspace = os.getenv("GITHUB_WORKSPACE", ".")
            filename = f"prices_{set_code.lower()}.json"
            out_path = os.path.join(workspace, filename)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(prices, f, indent=2, ensure_ascii=False)
            print(f"✅ Gespeichert: {filename}")
        except Exception as e:
            print(f"❌ JSON Parse Error: {e}")
    else:
        print(f"❌ HTTP Error {response.status_code} for {set_code}")

def main():
    print(f"🔁 Starte Preis-Update {datetime.utcnow().isoformat()} UTC")
    for code in SETS:
        download_prices(code)

if __name__ == "__main__":
    main()
