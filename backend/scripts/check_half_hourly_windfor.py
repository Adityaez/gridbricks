"""Check if WINDFOR has any 30-minute intervals or strictly hourly."""
import httpx

client = httpx.Client(timeout=30.0)
url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"
params = {
    "publishDateTimeFrom": "2026-01-01T00:00:00Z",
    "publishDateTimeTo": "2026-01-03T00:00:00Z"
}
r = client.get(url, params=params)
data = r.json()
print("Total records fetched:", len(data))
non_zero_minute_start_times = [d for d in data if not d["startTime"].endswith(":00:00Z")]
print("Records with non-00 minute start times:", len(non_zero_minute_start_times))
if non_zero_minute_start_times:
    print("Example non-00 minute start time:", non_zero_minute_start_times[0])
