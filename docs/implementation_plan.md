# WindSight --- Phase-Wise Implementation Plan

**Product:** WindSight --- Day-Ahead Wind Forecast Intelligence  
**Document:** `implementation_plan.md`  
**Location:** `c:\gridbricks\docs\implementation_plan.md`  
**Target Scope:** January 2026 Elexon BMRS Datasets (`FUELHH` & `WINDFOR`)  
**Total Time Budget:** 16 Hours (15.0h Execution + 1.0h Contingency Buffer)  
**Primary References:** `prd.md`, `techstack.md`

---

## 1. Executive Summary & System Architecture

WindSight is an analytical web application engineered for a UK electricity utility's day-ahead procurement desk. The tool enables power traders and procurement analysts to:
1. Reconstruct historical decision-time forecast states strictly before business cutoffs (eliminating look-ahead bias).
2. Compare selected forecasts against realized half-hourly wind generation (`FUELHH`, `fuelType = WIND`).
3. Compute standardized accuracy metrics (MAE, RMSE, Signed Bias, WAPE).
4. Inspect data coverage, missingness, and forecast publication histories.

### High-Level Architecture Flow

```
+-----------------------------------------------------------------------------------+
|                               ELEXON BMRS API                                     |
|  - FUELHH (Half-hourly generation by fuel type: WIND)                             |
|  - WINDFOR (Wind generation forecasts with publishTime & startTime)              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v (HTTPX Client / Bounded Date Ranges)
+-----------------------------------------------------------------------------------+
|                        FASTAPI BACKEND SERVICE                                    |
|                                                                                   |
|  +----------------------------+       +----------------------------------------+  |
|  | Ingestion & Normalization  | ----> | Analytics & Forecast Selection Engine  |  |
|  | - UTC Timestamps           |       | - Cutoff Filter: publishTime <= C(t)   |  |
|  | - fuelType = WIND filter   |       | - Latest eligible forecast selector    |  |
|  | - Deterministic Deduplication      | - Error & Metrics: MAE, RMSE, Bias,WAPE|  |
|  +----------------------------+       +----------------------------------------+  |
|                                                    |                              |
|                                                    v                              |
|  +-----------------------------------------------------------------------------+  |
|  | Pydantic Schemas & REST Endpoints:                                          |  |
|  |   GET /api/health                                                           |  |
|  |   GET /api/dashboard?date=YYYY-MM-DD                                        |  |
|  |   GET /api/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD                          |  |
|  |   GET /api/forecast-evolution?date=YYYY-MM-DD                               |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v (JSON REST API / CORS Enabled)
+-----------------------------------------------------------------------------------+
|                       REACT + VITE FRONTEND (Vercel)                              |
|  - Date Picker (Restricted strictly to January 2026)                              |
|  - Configurable Decision Cutoff Parameter Display                                 |
|  - Executive KPI Cards (MAE, RMSE, Signed Bias, WAPE, Matched Interval Count)     |
|  - Recharts Dual-Line Actual vs. Forecast Time Series (30-min intervals)          |
|  - Detailed Interval Table (startTime, publishTime, forecast, actual, error)     |
|  - Missing Data, Empty State, and Error Banners                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Operational Rules & Mathematical Standards

### 2.1 Look-Ahead Bias Prevention
For any delivery interval starting at $t$:
- Decision cutoff: $C(t) = t - \Delta_{\text{cutoff}}$ (Default pilot assumption: Day-Ahead 17:00 UTC on $D-1$, configurable via query/config).
- Eligible forecasts subset: 
  $$\mathcal{F}_{\text{eligible}}(t) = \{ f \in \text{WINDFOR} \mid f.\text{startTime} = t \land f.\text{publishTime} \le C(t) \}$$
- Decision-time forecast selected:
  $$F(t) = \operatorname{argmax}_{f \in \mathcal{F}_{\text{eligible}}(t)} (f.\text{publishTime})$$
- If $\mathcal{F}_{\text{eligible}}(t) = \emptyset$, the interval must be flagged as `MISSING_FORECAST`. Under no circumstances may a forecast published after $C(t)$ be substituted.

### 2.2 Accuracy Metrics (Calculated over $n$ valid matched pairs)
- **Signed Error:** $e_i = F_i - A_i$ (Positive = over-forecast; Negative = under-forecast)
- **Mean Absolute Error (MAE):** 
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |F_i - A_i|$$
- **Root Mean Squared Error (RMSE):** 
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (F_i - A_i)^2}$$
- **Signed Bias:** 
  $$\text{Bias} = \frac{1}{n} \sum_{i=1}^n (F_i - A_i)$$
- **Weighted Absolute Percentage Error (WAPE):**
  $$\text{WAPE} = \frac{\sum_{i=1}^n |F_i - A_i|}{\sum_{i=1}^n A_i} \times 100\% \quad (\text{if } \sum A_i > 0; \text{ else } \text{null})$$

---

## 3. Phase-Wise Implementation Roadmap

```
+---------------------------------------------------------------------------------------+
| PHASE 0: Project Setup & Repo Initialization                              (0.5 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 1: Elexon API Discovery, Schemas & Validation                       (1.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 2: Backend Data Ingestion & Normalization Layer                     (2.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 3: Analytics Engine & Cutoff Selection Logic                        (2.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 4: FastAPI REST Endpoints & Route Contracts                         (1.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 5: React Dashboard UI & Visualizations                              (3.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 6: End-to-End Integration, Dockerization & Test Verification        (1.5 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 7: Technical Documentation, AI Disclosure & GitHub Cleanliness       (1.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 8: Production Deployment (Vercel & Python Host)                     (1.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
| PHASE 9: Demonstration Video & Final Form Submission                      (2.0 Hours) |
+---------------------------------------------------------------------------------------+
                                           |
                    Total Planned Time: 15.0h / 16.0h (1.0h Buffer)
```

---

### Phase 0: Project Setup & Scope Confirmation
**Time Budget:** 0.5 Hours (30 mins)  
**Objective:** Establish directory structure, baseline repositories, clean environments, and configuration boundaries.

#### Actionable Steps:
1. **Initialize Directory Tree:**
   ```text
   windsight/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── main.py
   │   │   ├── schemas.py
   │   │   ├── config.py
   │   │   ├── api/
   │   │   │   ├── __init__.py
   │   │   │   └── routes.py
   │   │   └── services/
   │   │       ├── __init__.py
   │   │       ├── elexon.py
   │   │       └── analytics.py
   │   ├── tests/
   │   │   ├── __init__.py
   │   │   ├── conftest.py
   │   │   ├── test_analytics.py
   │   │   └── test_api.py
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── frontend/
   │   ├── src/
   │   │   ├── components/
   │   │   │   ├── MetricCard.tsx
   │   │   │   ├── ForecastChart.tsx
   │   │   │   ├── ForecastTable.tsx
   │   │   │   ├── CoverageSummary.tsx
   │   │   │   └── DateSelector.tsx
   │   │   ├── services/
   │   │   │   └── api.ts
   │   │   ├── types/
   │   │   │   └── index.ts
   │   │   ├── App.tsx
   │   │   └── main.tsx
   │   ├── index.html
   │   ├── package.json
   │   ├── vite.config.ts
   │   ├── tsconfig.json
   │   └── Dockerfile
   ├── docs/
   │   ├── prd.md
   │   ├── techstack.md
   │   └── implementation_plan.md
   ├── docker-compose.yml
   ├── .env.example
   ├── .gitignore
   └── README.md
   ```
2. **Git & Security Initialization:**
   - Configure `.gitignore` to prevent leaking `.env`, `node_modules`, `__pycache__`, `.pytest_cache`, `.venv`, `.DS_Store`.
   - Setup `.env.example` with:
     ```bash
     ELEXON_API_KEY=
     BACKEND_CORS_ORIGINS=["http://localhost:5173", "https://*.vercel.app"]
     DEFAULT_CUTOFF_RULE=day_ahead_1700
     VITE_API_BASE_URL=http://localhost:8000
     ```
3. **Verify Constraints:**
   - Strict temporal guard: January 1, 2026 00:00 UTC to January 31, 2026 23:59 UTC.
   - Strictly national aggregated data (`WIND`).

#### Deliverables & Exit Criteria:
- Clean Git workspace initialized.
- Environment templates and directory skeletons created.
- Scope bounds strictly recorded.

---

### Phase 1: Elexon API Discovery, Schemas & Validation
**Time Budget:** 1.0 Hours  
**Objective:** Confirm live API response formats, parameter names, date formatting, pagination limits, and rate-limits for `FUELHH` and `WINDFOR`.

#### Actionable Steps:
1. **API Probe Script (`backend/scripts/probe_elexon.py`):**
   - Query endpoint: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream`
   - Query endpoint: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream`
   - Test date parameters: `publishDateTimeFrom`, `publishDateTimeTo`, `settlementDateFrom`, `settlementDateTo` (confirm whether ISO-8601 or `YYYY-MM-DD`).
2. **Inspect & Document Response Payload:**
   - Inspect `FUELHH`: Verify `fuelType == "WIND"`, verify units (MW or MWh per half hour), timestamp fields (`startTime`, `settlementDate`, `settlementPeriod`).
   - Inspect `WINDFOR`: Verify `startTime` (delivery period start), `publishTime` (time forecast was issued), `generation` (forecast MW value).
3. **Analyze Edge Constraints:**
   - Confirm timezone format (Elexon uses UTC timestamps with `Z` or `+00:00`).
   - Check maximum record count per stream query. If pagination or streaming limit applies, implement day-chunked queries (`from=YYYY-MM-DD&to=YYYY-MM-DD`).
   - Store sample payloads as fixtures under `backend/tests/fixtures/` for deterministic offline testing.

#### Deliverables & Exit Criteria:
- Confirmed API parameter schemas and parsing logic.
- Recorded example payloads in tests directory.
- Documented fallback/retry policy for rate limits or transient outages.

---

### Phase 2: Backend Data Ingestion & Normalization Layer
**Time Budget:** 2.0 Hours  
**Objective:** Implement robust async HTTP ingestion using HTTPX, deterministic parsing, timezone normalization, and caching.

#### Actionable Steps:
1. **Elexon Client (`backend/app/services/elexon.py`):**
   - Implement `ElexonClient` class with HTTPX async client.
   - Methods:
     - `fetch_actual_wind(start_date: date, end_date: date) -> pd.DataFrame`
     - `fetch_wind_forecasts(start_date: date, end_date: date) -> pd.DataFrame`
   - Resilience: Configure 15s timeout, 3 bounded exponential retries on status codes 429, 500, 502, 503, 504.
2. **Normalization & Cleaning Pipeline:**
   - Standardize all timestamps to ISO-8601 UTC (`datetime64[ns, UTC]`).
   - Filter `FUELHH` strictly by `fuelType.str.upper() == "WIND"`.
   - Validate numerical bounds: $generation \ge 0$. Reject or flag anomalous null values.
   - Deterministic Deduplication Policy: If duplicate `(startTime, publishTime)` records occur, retain the record with latest ingestion timestamp or highest revision index; document rule in code.
3. **Optional In-Memory Caching:**
   - Implement lightweight LRU or dictionary cache keyed by `(dataset, date)` to avoid refetching static historical January 2026 data on every request.

#### Deliverables & Exit Criteria:
- Unit test verified ingestion functions capable of transforming raw Elexon JSON into clean, normalized Pandas DataFrames.
- Zero look-ahead bias leakage at ingestion stage.

---

### Phase 3: Analytics Engine & Cutoff Selection Logic
**Time Budget:** 2.0 Hours  
**Objective:** Build the core algorithmic brain of WindSight: cutoff evaluation, matching, error metrics, and coverage summaries.

#### Actionable Steps:
1. **Cutoff Decision Logic (`backend/app/services/analytics.py`):**
   - Implement configurable cutoff strategies:
     - `day_ahead_1700`: For interval $t$ on day $D$, $C(t) = (D-1) \text{ 17:00 UTC}$.
     - `fixed_lead_hours`: $C(t) = t - \text{hours}$.
     - `gate_closure`: $C(t) = t - 1\text{ hour}$.
   - Filter forecast records: Keep only records where $\text{publishTime} \le C(t)$.
   - Group by delivery interval $\text{startTime}$ and pick $\max(\text{publishTime})$.
2. **Interval Matching:**
   - Perform outer or left join between all expected 48 half-hour settlement periods (or 50 if clock-change, not applicable in Jan) and actual/forecast data.
   - Status classifications:
     - `MATCHED`: Both selected forecast and actual generation present.
     - `MISSING_FORECAST`: Actual present, no forecast published before cutoff.
     - `MISSING_ACTUAL`: Forecast present, actual missing from FUELHH.
     - `MISSING_BOTH`: Neither available.
3. **Metric Calculation Engine:**
   - Filter strictly to `MATCHED` pairs ($n$).
   - Compute `error = forecast - actual`.
   - Compute MAE, RMSE, Signed Bias.
   - Compute WAPE: If $\sum A_i > 0$, $\text{WAPE} = \frac{\sum |e_i|}{\sum A_i} \times 100$; otherwise return `None` (JSON `null`).
   - Data Coverage: Output total expected intervals (48 per day), matched count, missing forecast count, missing actual count.
4. **Deterministic Unit Testing (`backend/tests/test_analytics.py`):**
   - Test 1: Future forecast published after cutoff is strictly excluded.
   - Test 2: When multiple valid forecasts exist, the latest pre-cutoff forecast is chosen.
   - Test 3: Standard metrics against hand-calculated vector:
     - Forecast: $[100, 200, 300]$, Actual: $[120, 180, 300]$
     - Errors: $[-20, +20, 0]$
     - MAE = $40 / 3 \approx 13.33$, RMSE = $\sqrt{800/3} \approx 16.33$, Bias = $0$, WAPE = $40 / 600 = 6.67\%$.
   - Test 4: Denominator zero handling for WAPE.
   - Test 5: Incomplete day / missing forecast interval handling.

#### Deliverables & Exit Criteria:
- 100% test coverage on `analytics.py` with passing pytest assertions.

---

### Phase 4: FastAPI REST Endpoints & Route Contracts
**Time Budget:** 1.0 Hours  
**Objective:** Expose clean, strongly typed OpenAPI-compliant JSON routes with query parameter validation.

#### Actionable Steps:
1. **Pydantic Schemas (`backend/app/schemas.py`):**
   ```python
   class IntervalDataPoint(BaseModel):
       interval_start: datetime
       interval_end: datetime
       settlement_period: int
       forecast_mw: Optional[float]
       publish_time: Optional[datetime]
       actual_mw: Optional[float]
       error_mw: Optional[float]
       status: Literal["MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL", "MISSING_BOTH"]

   class MetricsSummary(BaseModel):
       mae_mw: Optional[float]
       rmse_mw: Optional[float]
       bias_mw: Optional[float]
       wape_percent: Optional[float]
       total_expected: int
       matched_intervals: int
       missing_forecasts: int
       missing_actuals: int

   class DashboardResponse(BaseModel):
       delivery_date: date
       cutoff_applied: str
       metrics: MetricsSummary
       intervals: List[IntervalDataPoint]

   class AggregateAnalyticsResponse(BaseModel):
       date_from: date
       date_to: date
       metrics: MetricsSummary
       daily_breakdown: List[DailyMetricItem]
   ```
2. **API Routes (`backend/app/api/routes.py`):**
   - `GET /api/health`: Return `{"status": "ok", "timestamp": "...", "version": "1.0.0"}`.
   - `GET /api/dashboard?date=YYYY-MM-DD&cutoff_rule=...`:
     - Validate $2026-01-01 \le \text{date} \le 2026-01-31$. Return 400 for out-of-range dates.
     - Fetch actuals and forecasts for that day.
     - Execute analytics and return `DashboardResponse`.
   - `GET /api/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`:
     - Return aggregate metrics over multiple days in January 2026.
   - `GET /api/forecast-evolution?date=YYYY-MM-DD`:
     - Return publication trace across time showing how forecasts shifted closer to gate closure.
3. **CORS & Middleware Configuration:**
   - Allow requests from `http://localhost:5173` and deployed Vercel domains.

#### Deliverables & Exit Criteria:
- Swagger UI (`/docs`) operational with interactive schema documentation.
- All edge status codes (400 on invalid date range, 404/502 on upstream missing) tested.

---

### Phase 5: React Dashboard UI & Visualizations
**Time Budget:** 3.0 Hours  
**Objective:** Construct a high-performance, intuitive day-ahead forecast analysis dashboard with Recharts, responsive layouts, and zero placeholder data.

#### Actionable Steps:
1. **Vite + React Setup (`frontend/`):**
   - Clean setup with TypeScript and Tailwind CSS or structured CSS Modules.
   - Configure API client service with base URL fallback (`VITE_API_BASE_URL || ''`).
2. **Core UI Components:**
   - **Header & Scope Banner:** Display title **WindSight --- Day-Ahead Wind Forecast Intelligence**, January 2026 Pilot indicator, and decision cutoff configuration badge.
   - **Date Selector:** Calendar control restricted between `2026-01-01` and `2026-01-31`, with quick-navigation buttons (Previous Day, Next Day).
   - **KPI Metric Strip (`MetricCard.tsx`):**
     - Display MAE (MW), RMSE (MW), Signed Bias (MW), WAPE (%), Matched Interval count.
     - Subtle color coding for Bias (amber for over-forecast, cyan/blue for under-forecast).
     - Tooltips with mathematical formulas explaining each metric.
   - **Actual vs Forecast Chart (`ForecastChart.tsx`):**
     - Recharts ResponsiveContainer with dual lines/areas:
       - Actual Wind Generation (Solid Green / Teal line, dot markers).
       - Decision-Time Forecast (Dashed Blue line).
       - Error Area or secondary bar indicator.
     - Custom Tooltip showing interval timestamp, delivery half-hour, forecast MW, publish time, actual MW, and delta.
   - **Settlement Interval Table (`ForecastTable.tsx`):**
     - 48 rows showing: Period (1-48), Start Time (UTC), Selected Forecast (MW), Forecast Publish Time, Actual Realized (MW), Signed Error (MW), Status Badge.
     - Sorting and status filtering (All, Missing only).
   - **Coverage & Missing Data Notice (`CoverageSummary.tsx`):**
     - Clear banner if any intervals have missing forecasts or actuals.
   - **Forecast Evolution Tab/Toggle (if supported by data):**
     - Shows how forecasts evolved at different publication timestamps prior to gate closure.
3. **State Management & UX Edge States:**
   - Loading skeletons / spinner during fetch.
   - Empty state when no data exists for selected parameters.
   - Error banner with human-readable error if Elexon API is unreachable.

#### Deliverables & Exit Criteria:
- Interactive UI rendering genuine backend metrics without console errors.
- Fully responsive on standard laptop (1366x768) and desktop (1920x1080) resolutions.

---

### Phase 6: End-to-End Integration, Dockerization & Test Verification
**Time Budget:** 1.5 Hours  
**Objective:** Containerize the full stack, verify seamless frontend-to-backend communication, and validate against end-to-end user journeys.

#### Actionable Steps:
1. **Backend Container (`backend/Dockerfile`):**
   - Python 3.11-slim base image.
   - Install dependencies via `requirements.txt`.
   - Expose port 8000.
   - Launch command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
2. **Frontend Container (`frontend/Dockerfile`):**
   - Multi-stage build: Node 20-alpine build stage, Nginx unprivileged or lightweight server to serve static assets, OR Node development container for local compose.
3. **Compose Orchestration (`docker-compose.yml`):**
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
         - DEFAULT_CUTOFF_RULE=day_ahead_1700
       restart: unless-stopped

     frontend:
       build: ./frontend
       ports:
         - "5173:5173"
       environment:
         - VITE_API_BASE_URL=http://localhost:8000
       depends_on:
         - backend
       restart: unless-stopped
   ```
4. **Integration Verification Protocol:**
   - Execute `docker compose up --build`.
   - Verify health check: `curl http://localhost:8000/api/health`.
   - Open browser at `http://localhost:5173`, select `2026-01-15`, confirm data renders properly.
   - Run full Pytest test suite: `pytest backend/tests/ -v`.

#### Deliverables & Exit Criteria:
- One-command startup via `docker compose up`.
- Zero CORS errors or asset bundling bugs.
- All test suites passing.

---

### Phase 7: Technical Documentation, AI Disclosure & GitHub Cleanliness
**Time Budget:** 1.0 Hours  
**Objective:** Prepare a submission-grade, anonymized public GitHub repository with comprehensive README, data transparency notes, and mandatory AI disclosures.

#### Actionable Steps:
1. **GitHub Repository Preparation:**
   - Create public repository with an anonymized/random-like name (e.g., `ws-procure-intelligence-26` or `grid-windsight-eval`).
   - Audit git history to ensure no `.env`, internal credentials, or proprietary tokens are present.
2. **Comprehensive `README.md` Drafting:**
   - Project Overview: Day-Ahead Wind Forecast Intelligence for UK Electricity Procurement desk.
   - Architectural Diagram & Request Flow.
   - Live Deployed Demo Link & Credentials (if any).
   - Quickstart Guide (Local Python/Node execution & Docker Compose execution).
   - Mathematical Definitions (MAE, RMSE, Signed Bias, WAPE formulas).
   - Look-Ahead Bias Mitigation: Explicit documentation of cutoff logic ($publishTime \le C(t)$).
   - Assumptions & Scope Boundaries: January 2026 historical pilot, no consumer demand modeling, no price/trading P&L speculation.
   - API Reference Documentation: Summary of endpoints and sample payloads.
3. **Mandatory AI-Use Disclosure:**
   - Specify tools used (e.g., Google Antigravity / Gemini 3.8 Flash, GitHub Copilot).
   - Detail specific assistance areas: Boilerplate scaffolding, test fixture generation, mathematical validation, and documentation formatting.
   - Affirm that all analytical calculations and cutoff logic were verified with deterministic unit tests.

#### Deliverables & Exit Criteria:
- Polished, professional README.
- Clean git history with descriptive atomic commit messages.

---

### Phase 8: Production Deployment
**Time Budget:** 1.0 Hours  
**Objective:** Deploy backend and frontend to stable public cloud hosts and verify live functionality.

#### Actionable Steps:
1. **Backend Deployment (Render / Fly.io / Railway / Cloud Run):**
   - Deploy backend container or FastAPI service.
   - Set environment variables (`PORT`, `BACKEND_CORS_ORIGINS`).
   - Confirm public health check responds at `https://<backend-app>.onrender.com/api/health`.
2. **Frontend Deployment (Vercel):**
   - Connect GitHub repo or deploy via Vercel CLI.
   - Set environment variable: `VITE_API_BASE_URL=https://<backend-app>.onrender.com`.
   - Configure single-page app rewrite rule in `vercel.json` if needed.
3. **End-to-End Live Smoke Test:**
   - Open deployed frontend in an incognito/private browser tab.
   - Verify date selection across multiple January 2026 dates (e.g., 2026-01-05, 2026-01-15, 2026-01-28).
   - Verify browser console is free of CORS, WebSocket, or 404 errors.
   - Inspect network payloads to ensure live data is being loaded.

#### Deliverables & Exit Criteria:
- Publicly accessible, responsive live frontend backed by live deployed API.

---

### Phase 9: Demonstration Video & Final Form Submission
**Time Budget:** 2.0 Hours  
**Objective:** Record and publish a concise 10-minute video walkthrough (customer pitch + technical deep dive) and complete the formal evaluation submission form.

#### Actionable Steps:
1. **Video Demo Plan (Strict 10-Minute Limit):**
   - **Part 1: Customer Pitch (Max 5:00 mins):**
     - *0:00 - 1:00:* Introduce the business problem: Day-ahead UK wind volatility, risks of balancing mechanism penalties, and why post-cutoff forecast leaks distort accuracy evaluation.
     - *1:00 - 2:30:* Walk through the WindSight dashboard for a specific January 2026 delivery day. Highlight the selected forecast, publication timestamp, and decision cutoff.
     - *2:30 - 3:45:* Demonstrate the Forecast vs. Actual generation chart and explain the KPI metrics (MAE, RMSE, Bias, WAPE).
     - *3:45 - 5:00:* Address business value and explicit pilot limitations: Historical January 2026 evaluation, no demand/price speculation, pure wind accuracy transparency.
   - **Part 2: Technical Deep Dive (Max 5:00 mins):**
     - *5:00 - 6:00:* Architecture overview: React/Vite, FastAPI, Pandas, Elexon BMRS API.
     - *6:00 - 7:15:* Code walkthrough of `analytics.py`: Show how `publishTime <= C(t)` prevents look-ahead bias and explain deduplication.
     - *7:15 - 8:30:* Show test suite execution (`pytest`) demonstrating metric verification, edge cases (zero denominator, missing forecasts).
     - *8:30 - 9:30:* Docker configuration, deployment topology, and error resilience.
     - *9:30 - 10:00:* Summary of trade-offs and future production roadmap.
2. **Publish & Verify Video:**
   - Upload video to YouTube with visibility set to **Unlisted**.
   - Verify audio clarity and 1080p video rendering in an incognito window.
3. **Submission Form Completion:**
   - Access official submission form: `https://forms.cloud.microsoft/r/FTX6K2bbnU`
   - Input: Public GitHub repository URL, deployed web app URL, Unlisted YouTube video URL.
   - Verify all URLs are publicly accessible without authentication.

#### Deliverables & Exit Criteria:
- Completed submission form.
- Recorded and verified unlisted video demonstration.

---

## 4. Time Budget & Milestone Tracking Matrix

| Phase | Description | Budget | Target Completion Point | Status |
|---|---|---|---|---|
| **Phase 0** | Project Setup & Scope Confirmation | 0.5 h | T + 0.5 h | Planned |
| **Phase 1** | Elexon API Discovery & Validation | 1.0 h | T + 1.5 h | Planned |
| **Phase 2** | Backend Data Ingestion & Normalization | 2.0 h | T + 3.5 h | Planned |
| **Phase 3** | Analytics Engine & Cutoff Selection | 2.0 h | T + 5.5 h | Planned |
| **Phase 4** | Backend REST Endpoints & Contracts | 1.0 h | T + 6.5 h | Planned |
| **Phase 5** | React Dashboard UI & Visualizations | 3.0 h | T + 9.5 h | Planned |
| **Phase 6** | Integration, Docker & Quality Checks | 1.5 h | T + 11.0 h | Planned |
| **Phase 7** | README, AI Disclosure & GitHub Repo | 1.0 h | T + 12.0 h | Planned |
| **Phase 8** | Production Cloud Deployment | 1.0 h | T + 13.0 h | Planned |
| **Phase 9** | Video Demo (10 min) & Form Submission | 2.0 h | T + 15.0 h | Planned |
| **Buffer** | Contingency & Troubleshooting | 1.0 h | T + 16.0 h | Reserved |
| **TOTAL** | **Full Project Delivery** | **16.0 h** | | |

---

## 5. Risk Assessment & Contingency Plan

| Risk / Roadblock | Severity | Mitigation Strategy |
|---|---|---|
| **Elexon API Rate Limiting / 429 Errors** | Medium | Implement chunked daily queries and bounded exponential backoff in `elexon.py`. Cache normalized January 2026 payloads locally in backend memory. |
| **Missing Forecast Revisions for Certain Intervals** | Low | Flag intervals clearly as `MISSING_FORECAST` in table and KPI summaries; never backfill with future forecasts or zeros. |
| **Zero Generation in Denominator for WAPE** | Low | Implement guard condition in `analytics.py`: return `None` (JSON `null`) and render "N/A" on the UI card with tooltip explanation. |
| **Deployment Platform Cold Start / Sleeps** | Medium | Select low-latency container host or implement keep-alive ping; add frontend loading spinners and retry prompts. |
| **Video Recording Over-Run (>10 min)** | High | Use a strict slide/script outline with a visible stopwatch timer; record customer pitch and tech review in targeted 4.5-minute blocks. |

---

## 6. Definition of Done (Final Project Checklist)

- [ ] Supported date range is strictly verified for 1–31 January 2026.
- [ ] Actual wind generation correctly isolated from `FUELHH` (`fuelType = WIND`).
- [ ] Forecast data ingested from `WINDFOR` with `startTime`, `publishTime`, and `generation`.
- [ ] Decision-time forecast selection strictly enforces $publishTime \le C(t)$ without look-ahead bias.
- [ ] MAE, RMSE, Signed Bias, and WAPE are mathematically verified via automated tests.
- [ ] Dashboard displays genuine backend data (no fabricated placeholders).
- [ ] Loading, missing-data, and error states render gracefully on the frontend.
- [ ] Automated unit tests pass cleanly in Pytest.
- [ ] Full application runs locally via `docker compose up`.
- [ ] Public GitHub repository is clean, documented, and includes mandatory AI disclosures.
- [ ] Production frontend and backend are deployed and live on public URLs.
- [ ] 10-minute unlisted YouTube walkthrough is recorded, verified, and submitted via the Microsoft Form.

