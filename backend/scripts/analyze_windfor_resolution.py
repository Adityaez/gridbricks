"""Analyze WINDFOR resolution and interval steps."""
import httpx

client = httpx.Client(timeout=30.0)
url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"
params = {
    "publishDateTimeFrom": "2026-01-14T15:00:00Z",
    "publishDateTimeTo": "2026-01-14T16:00:00Z"
}
r = client.get(url, params=params)
data = r.json()
print("Sample publication records count:", len(data))
if data:
    pub_times = sorted(set(d["publishTime"] for d in data))
    print("Unique publish times in this 1h slice:", pub_times)
    first_pub = pub_times[0]
    first_batch = [d for d in data if d["publishTime"] == first_pub]
    print(f"Number of forecast intervals in single publication {first_pub}:", len(first_batch))
    first_batch = sorted(first_batch, key=lambda x: x["startTime"])
    for d in first_batch[:10]:
        print("  startTime:", d["startTime"], "generation:", d["generation"])
