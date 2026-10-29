"""Investigate WINDFOR query parameters and date filtering behavior."""
import json
import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def probe_windfor_params():
    client = httpx.Client(timeout=30.0, headers={"Accept": "application/json"})
    
    test_queries = [
        # Query 1: settlementDateFrom / settlementDateTo
        {"name": "settlementDate", "params": {"settlementDateFrom": "2026-01-15", "settlementDateTo": "2026-01-15"}},
        # Query 2: publishDateTimeFrom / publishDateTimeTo
        {"name": "publishDateTime", "params": {"publishDateTimeFrom": "2026-01-14T00:00:00Z", "publishDateTimeTo": "2026-01-14T23:59:59Z"}},
        # Query 3: check if there is a startTimeFrom / startTimeTo or similar
        {"name": "startTime", "params": {"startTimeFrom": "2026-01-15T00:00:00Z", "startTimeTo": "2026-01-15T23:59:59Z"}},
    ]

    for q in test_queries:
        url = f"{BASE_URL}/datasets/WINDFOR/stream"
        print(f"\n--- Testing WINDFOR with {q['name']}: {q['params']} ---")
        try:
            r = client.get(url, params=q["params"])
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"Returned records: {len(data)}")
                if len(data) > 0:
                    start_times = [d.get("startTime") for d in data if "startTime" in d]
                    publish_times = [d.get("publishTime") for d in data if "publishTime" in d]
                    print(f"Sample item: {json.dumps(data[0], indent=2)}")
                    if start_times:
                        print(f"Start times range: min={min(start_times)}, max={max(start_times)}")
                    if publish_times:
                        print(f"Publish times range: min={min(publish_times)}, max={max(publish_times)}")
            else:
                print(f"Error text: {r.text[:200]}")
        except Exception as e:
            print(f"Failed: {e}")

    # Also test FUELHH for WIND filter
    print("\n--- Testing FUELHH for settlementDate 2026-01-15 ---")
    r = client.get(f"{BASE_URL}/datasets/FUELHH/stream", params={"settlementDateFrom": "2026-01-15", "settlementDateTo": "2026-01-15"})
    if r.status_code == 200:
        data = r.json()
        print(f"Total FUELHH records: {len(data)}")
        wind_records = [d for d in data if d.get("fuelType", "").upper() == "WIND"]
        print(f"WIND records count: {len(wind_records)}")
        if wind_records:
            print("First WIND record:", json.dumps(wind_records[0], indent=2))
            print("Last WIND record:", json.dumps(wind_records[-1], indent=2))
            gen_values = [d.get("generation") for d in wind_records]
            print(f"Generation stats: min={min(gen_values)}, max={max(gen_values)}, sum={sum(gen_values)}")

if __name__ == "__main__":
    probe_windfor_params()
