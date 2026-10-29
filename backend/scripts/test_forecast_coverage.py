"""Check forecast availability for delivery date 2026-01-15."""
import json
import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def check_forecast_coverage():
    client = httpx.Client(timeout=30.0, headers={"Accept": "application/json"})
    
    # Let's query publications from 2026-01-13T00:00:00Z to 2026-01-15T23:59:59Z
    # to capture day-ahead forecasts (and evolution) for delivery date 2026-01-15
    url = f"{BASE_URL}/datasets/WINDFOR/stream"
    params = {
        "publishDateTimeFrom": "2026-01-13T00:00:00Z",
        "publishDateTimeTo": "2026-01-15T23:59:59Z"
    }
    
    print(f"Fetching WINDFOR with params: {params}")
    r = client.get(url, params=params)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Total WINDFOR records fetched: {len(data)}")
    
    # Filter for intervals where startTime falls on 2026-01-15
    d15_forecasts = [
        d for d in data 
        if d.get("startTime", "").startswith("2026-01-15")
    ]
    print(f"Forecast records for delivery date 2026-01-15: {len(d15_forecasts)}")
    
    if d15_forecasts:
        # Check distinct delivery intervals covered
        delivery_intervals = sorted(set(d["startTime"] for d in d15_forecasts))
        print(f"Distinct delivery intervals covered on 2026-01-15: {len(delivery_intervals)} of 48")
        print(f"First interval: {delivery_intervals[0]}, Last interval: {delivery_intervals[-1]}")
        
        # Check cutoff rule: Day-ahead cutoff = 2026-01-14T17:00:00Z
        cutoff_str = "2026-01-14T17:00:00Z"
        pre_cutoff = [d for d in d15_forecasts if d["publishTime"] <= cutoff_str]
        print(f"Forecasts published on or before cutoff {cutoff_str}: {len(pre_cutoff)}")
        
        pre_cutoff_intervals = sorted(set(d["startTime"] for d in pre_cutoff))
        print(f"Distinct intervals with pre-cutoff forecasts: {len(pre_cutoff_intervals)} of 48")
        
        # Let's see an example of interval with multiple revisions
        sample_interval = delivery_intervals[0]
        revisions = [d for d in d15_forecasts if d["startTime"] == sample_interval]
        print(f"\nRevisions for interval {sample_interval}:")
        for rev in sorted(revisions, key=lambda x: x["publishTime"]):
            print(f"  Published: {rev['publishTime']} -> Forecast: {rev['generation']} MW")

if __name__ == "__main__":
    check_forecast_coverage()
