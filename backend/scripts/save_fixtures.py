"""Download and save clean, reproducible fixtures for January 15, 2026."""
import json
import os
import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def save_fixtures():
    os.makedirs("backend/tests/fixtures", exist_ok=True)
    client = httpx.Client(timeout=30.0, headers={"Accept": "application/json"})

    # 1. Fetch FUELHH for 2026-01-15
    print("Fetching FUELHH for 2026-01-15...")
    r = client.get(
        f"{BASE_URL}/datasets/FUELHH/stream",
        params={"settlementDateFrom": "2026-01-15", "settlementDateTo": "2026-01-15"}
    )
    if r.status_code == 200:
        fuelhh_records = r.json()
        print(f"Fetched {len(fuelhh_records)} FUELHH records.")
        with open("backend/tests/fixtures/fuelhh_2026_01_15.json", "w", encoding="utf-8") as f:
            json.dump(fuelhh_records, f, indent=2)
        print("Saved backend/tests/fixtures/fuelhh_2026_01_15.json")

    # 2. Fetch WINDFOR publications covering 2026-01-15 forecasts
    print("\nFetching WINDFOR publications for 2026-01-14...")
    r = client.get(
        f"{BASE_URL}/datasets/WINDFOR/stream",
        params={
            "publishDateTimeFrom": "2026-01-13T00:00:00Z",
            "publishDateTimeTo": "2026-01-15T23:59:59Z"
        }
    )
    if r.status_code == 200:
        windfor_records = r.json()
        print(f"Fetched {len(windfor_records)} WINDFOR records.")
        with open("backend/tests/fixtures/windfor_2026_01_15.json", "w", encoding="utf-8") as f:
            json.dump(windfor_records, f, indent=2)
        print("Saved backend/tests/fixtures/windfor_2026_01_15.json")

if __name__ == "__main__":
    save_fixtures()
