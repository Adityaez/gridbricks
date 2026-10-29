"""Elexon BMRS API exploration and probe script."""
import json
import os
import sys
import httpx

# Candidate base URLs for Elexon BMRS API
BASE_URL_INSIGHTS = "https://data.elexon.co.uk/bmrs/api/v1"
BASE_URL_DOCS = "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets"

def test_endpoints():
    print("=== Testing Elexon BMRS API Endpoints ===")
    headers = {
        "Accept": "application/json",
        "User-Agent": "WindSight-Research/1.0"
    }

    # Let's test actual generation FUELHH endpoint
    # Elexon Insights API v1 dataset stream endpoints:
    # GET https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=...&publishDateTimeTo=...
    # or settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01
    fuelhh_candidates = [
        f"{BASE_URL_INSIGHTS}/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01",
        f"{BASE_URL_INSIGHTS}/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-01T23:59:59Z",
        f"{BASE_URL_INSIGHTS}/datasets/FUELHH?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01",
        f"{BASE_URL_INSIGHTS}/generation/actual/per-type?from=2026-01-01&to=2026-01-01",
    ]

    client = httpx.Client(timeout=30.0, follow_redirects=True, headers=headers)

    fuelhh_data = None
    successful_fuelhh_url = None

    for url in fuelhh_candidates:
        print(f"\nProbing FUELHH: {url}")
        try:
            res = client.get(url)
            print(f"Status: {res.status_code}, Content-Type: {res.headers.get('content-type', '')}")
            if res.status_code == 200:
                try:
                    data = res.json()
                    print(f"Success! Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"Records count: {len(data)}")
                        if len(data) > 0:
                            print("Sample record keys:", list(data[0].keys()))
                            print("Sample record:", json.dumps(data[0], indent=2))
                    elif isinstance(data, dict):
                        print("Top-level keys:", list(data.keys()))
                        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                            print(f"Inner data count: {len(data['data'])}")
                            print("Sample record:", json.dumps(data["data"][0], indent=2))
                    fuelhh_data = data
                    successful_fuelhh_url = url
                    break
                except Exception as e:
                    print(f"JSON decode failed or stream text: {str(e)[:100]}")
                    print(f"Raw text sample: {res.text[:300]}")
            else:
                print(f"Response: {res.text[:200]}")
        except Exception as e:
            print(f"Request failed: {e}")

    # Now let's test WINDFOR endpoint
    windfor_candidates = [
        f"{BASE_URL_INSIGHTS}/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-31T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z",
        f"{BASE_URL_INSIGHTS}/datasets/WINDFOR/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01",
        f"{BASE_URL_INSIGHTS}/datasets/WINDFOR?publishDateTimeFrom=2025-12-31T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z",
        f"{BASE_URL_INSIGHTS}/forecast/generation/wind/latest",
        f"{BASE_URL_INSIGHTS}/forecast/generation/wind/peak",
        f"{BASE_URL_INSIGHTS}/forecast/generation/wind/evolution?settlementDate=2026-01-01",
    ]

    windfor_data = None
    successful_windfor_url = None

    for url in windfor_candidates:
        print(f"\nProbing WINDFOR: {url}")
        try:
            res = client.get(url)
            print(f"Status: {res.status_code}, Content-Type: {res.headers.get('content-type', '')}")
            if res.status_code == 200:
                try:
                    data = res.json()
                    print(f"Success! Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"Records count: {len(data)}")
                        if len(data) > 0:
                            print("Sample record keys:", list(data[0].keys()))
                            print("Sample record:", json.dumps(data[0], indent=2))
                    elif isinstance(data, dict):
                        print("Top-level keys:", list(data.keys()))
                        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                            print(f"Inner data count: {len(data['data'])}")
                            print("Sample record:", json.dumps(data["data"][0], indent=2))
                    windfor_data = data
                    successful_windfor_url = url
                    break
                except Exception as e:
                    print(f"JSON decode failed: {str(e)[:100]}")
                    print(f"Raw text sample: {res.text[:300]}")
            else:
                print(f"Response: {res.text[:200]}")
        except Exception as e:
            print(f"Request failed: {e}")

    # Let's save fixtures if we got data
    os.makedirs("backend/tests/fixtures", exist_ok=True)
    if fuelhh_data is not None:
        with open("backend/tests/fixtures/sample_fuelhh.json", "w", encoding="utf-8") as f:
            sample_records = fuelhh_data if isinstance(fuelhh_data, list) else fuelhh_data.get("data", fuelhh_data)
            json.dump(sample_records[:100] if isinstance(sample_records, list) else sample_records, f, indent=2)
        print("\nSaved backend/tests/fixtures/sample_fuelhh.json")

    if windfor_data is not None:
        with open("backend/tests/fixtures/sample_windfor.json", "w", encoding="utf-8") as f:
            sample_records = windfor_data if isinstance(windfor_data, list) else windfor_data.get("data", windfor_data)
            json.dump(sample_records[:100] if isinstance(sample_records, list) else sample_records, f, indent=2)
        print("Saved backend/tests/fixtures/sample_windfor.json")

if __name__ == "__main__":
    test_endpoints()
