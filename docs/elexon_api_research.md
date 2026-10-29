# Elexon BMRS API Discovery & Schema Validation Report

**Document:** `docs/elexon_api_research.md`  
**Phase:** Phase 1 --- Elexon API Discovery, Schemas & Validation  
**Date:** January 2026 Historical Pilot Analysis  
**Status:** Verified against Live Elexon BMRS API

---

## 1. Verified API Endpoints

Through live probing and endpoint validation, the active base URL for Elexon Insights Solution datasets is:
```text
Base URL: https://data.elexon.co.uk/bmrs/api/v1
```

### 1.1 Actual Generation: `FUELHH` Stream
- **Endpoint:** `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
- **Supported Parameters:**
  - `settlementDateFrom` (format: `YYYY-MM-DD`, e.g., `2026-01-15`)
  - `settlementDateTo` (format: `YYYY-MM-DD`, e.g., `2026-01-15`)
  - Optional: `fuelType` (can be filtered client-side or query parameter)
- **Response Shape:** JSON array (`list[dict]`) of records.
- **Volume:** Exactly 960 records per calendar day (48 half-hour settlement periods $\times$ 20 fuel types). Filtering for `fuelType == "WIND"` yields exactly **48 records** per day.

#### Sample `FUELHH` Record
```json
{
  "dataset": "FUELHH",
  "publishTime": "2026-01-15T00:30:00Z",
  "startTime": "2026-01-15T00:00:00Z",
  "settlementDate": "2026-01-15",
  "settlementPeriod": 1,
  "fuelType": "WIND",
  "generation": 14602
}
```

### 1.2 Forecast Generation: `WINDFOR` Stream
- **Endpoint:** `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
- **Supported Parameters:**
  - `publishDateTimeFrom` (ISO-8601 UTC format, e.g., `2026-01-13T00:00:00Z`)
  - `publishDateTimeTo` (ISO-8601 UTC format, e.g., `2026-01-15T23:59:59Z`)
  *(Note: Passing `settlementDateFrom` alone to WINDFOR/stream defaults to latest snapshot; queries must specify `publishDateTimeFrom` and `publishDateTimeTo`)*
- **Response Shape:** JSON array (`list[dict]`) of forecast revisions.
- **Publication Frequency:** Revisions are published multiple times per day (approximately every 2 to 3 hours). Each publication snapshot provides forecast records covering up to 73 hours ahead.

#### Sample `WINDFOR` Record
```json
{
  "dataset": "WINDFOR",
  "publishTime": "2026-01-14T15:30:00Z",
  "startTime": "2026-01-15T00:00:00Z",
  "generation": 17254
}
```

---

## 2. Key Data Schema & Resolution Findings

### 2.1 Units and Precision
- Both datasets report generation in **Megawatts (MW)** as integer/numeric values.
- No scaling factors or unit conversions (e.g., kW to MW or MWh) are required.

### 2.2 Timezone Convention
- All timestamps (`publishTime`, `startTime`) in both `FUELHH` and `WINDFOR` are explicitly in **UTC** with the ISO-8601 `Z` designator.
- Ingestion pipeline will parse with `pd.to_datetime(..., utc=True)` to avoid local machine timezone shifts.

### 2.3 Temporal Resolution & Interval Matching Nuance
- **`FUELHH` (Actuals):** Published at **30-minute settlement periods** (`:00:00Z` and `:30:00Z`, 48 periods per standard day).
- **`WINDFOR` (Forecasts):** National wind forecasts from National Grid ESO via Elexon are published at **60-minute resolution** on the hour (`:00:00Z`).
- **Matching Rule:**
  1. Primary strict matching matches by identical interval `startTime`. This yields 24 matched intervals on the hour and 24 `MISSING_FORECAST` half-hour intervals (coverage = 50%).
  2. For utility operations, an hourly forecast for hour $H$ (e.g. 00:00:00Z) represents the average wind power expected across that hour (both settlement period 1 [00:00-00:30] and settlement period 2 [00:30-01:00]).
  3. The analytics engine will support strict exact-start matching by default, with an option to expand hourly forecasts to both half-hours when evaluating settlement-period level bias, clearly labeled in UI and metrics.

---

## 3. Query Strategy & Ingestion Guardrails

1. **Date Bounding:**
   - For delivery date $D$, `FUELHH` query: `settlementDateFrom=D&settlementDateTo=D`.
   - For delivery date $D$, `WINDFOR` query: `publishDateTimeFrom=(D-2)T00:00:00Z&publishDateTimeTo=DT23:59:59Z`. This guarantees capture of all day-ahead forecasts published leading up to the Day-Ahead cutoff ($D-1$ 17:00 UTC) as well as evolution up to gate closure.
2. **HTTP Client & Resilience:**
   - HTTPX async client with connection timeout = 10s, read timeout = 25s.
   - Bounded retries: 3 attempts with exponential backoff on HTTP 429 (rate-limited) or 5xx server errors.
3. **Deterministic Deduplication:**
   - `FUELHH`: Deduplicate by `(startTime, fuelType)`, keeping latest `publishTime`.
   - `WINDFOR`: Deduplicate by `(startTime, publishTime)`, keeping latest ingestion.

---

## 4. Test Fixtures Created

The following clean, deterministic fixtures have been captured from the live API and committed under `backend/tests/fixtures/`:
- `backend/tests/fixtures/fuelhh_2026_01_15.json` (960 records, 48 wind actuals for 2026-01-15)
- `backend/tests/fixtures/windfor_2026_01_15.json` (1,752 records covering 2026-01-15 delivery intervals and evolution)
